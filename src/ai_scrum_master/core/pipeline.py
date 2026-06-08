from __future__ import annotations

from typing import Any, Callable

from ai_scrum_master.agents.crew import build_scrum_master_crew
from ai_scrum_master.agents.evaluator import EvaluatorAgent
from ai_scrum_master.agents.planner import PlannerAgent
from ai_scrum_master.agents.researcher import ResearcherAgent
from ai_scrum_master.actions.jira import JiraTool
from ai_scrum_master.actions.slack import SlackTool
from ai_scrum_master.core.agent_schemas import EvaluationOutput, PlannerStoryOutput, ResearchContextOutput, dump_model
from ai_scrum_master.core.config import get_runtime_profiles
from ai_scrum_master.core.context_selector import select_context_for_route
from ai_scrum_master.core.finalizer import blocked_actions, finalize_generation, should_block_planning
from ai_scrum_master.core.logging import get_logger
from ai_scrum_master.core.quality import (
    AMBIGUOUS_REQUEST,
    OVERSIZED_REQUEST,
    classify_requirement,
    validate_story_against_requirement,
)
from ai_scrum_master.core.requirement_router import route_requirement
from ai_scrum_master.core.story_validator import evaluate_planner_output, validate_post_generation

logger = get_logger(__name__)


def generate_story_pipeline(
    *,
    requirement: str,
    n_results: int = 5,
    allow_fallback_without_context: bool = False,
    forced_context_docs: list[str] | None = None,
    crew: "ScrumMasterCrew | None" = None,
    crewai_builder: Callable[..., Any] | None = None,
    progress_callback: Callable[[str, dict], None] | None = None,
    project_id: str | None = None,
) -> dict:
    builder = crewai_builder or (build_scrum_master_crew if crew is None else None)
    crewai_crew = builder(requirement, n_results=n_results) if builder else None
    crewai_output, crewai_warning = _kickoff_crewai_crew(
        crewai_crew,
        requirement=requirement,
        n_results=n_results,
        allow_fallback_without_context=allow_fallback_without_context,
    )
    crewai_result = _complete_crewai_response(crewai_output)
    if crewai_result is not None:
        final_result = _finalize_crewai_response(crewai_result, requirement)
        from ai_scrum_master.core.database import DatabaseManager
        DatabaseManager.save_history(requirement, final_result, project_id=project_id)
        return final_result

    runner = crew or ScrumMasterCrew()
    if crewai_crew is not None:
        runner.crewai_crew = crewai_crew
    result = runner.run(
        requirement=requirement,
        n_results=n_results,
        allow_fallback_without_context=allow_fallback_without_context,
        forced_context_docs=forced_context_docs,
        progress_callback=progress_callback,
        project_id=project_id,
    )
    if crewai_warning:
        result = _mark_crewai_failure_for_revision(result, crewai_warning)
        
    from ai_scrum_master.core.database import DatabaseManager
    DatabaseManager.save_history(requirement, result, project_id=project_id)
    
    return result


def _kickoff_crewai_crew(
    crewai_crew: Any,
    *,
    requirement: str,
    n_results: int,
    allow_fallback_without_context: bool,
) -> tuple[Any | None, str | None]:
    if crewai_crew is None or not hasattr(crewai_crew, "kickoff"):
        return None, None
    try:
        output = crewai_crew.kickoff(
            inputs={
                "requirement": requirement,
                "n_results": n_results,
                "allow_fallback_without_context": allow_fallback_without_context,
            }
        )
    except Exception as exc:
        logger.exception("CrewAI kickoff failed; deterministic finalizer will force revision")
        return None, f"CrewAI execution failed; output requires revision. Reason: {exc}"
    return output, None


def _complete_crewai_response(output: Any) -> dict | None:
    if isinstance(output, dict) and {"context", "story", "evaluation"}.issubset(output):
        return dict(output)
    return None


def _finalize_crewai_response(result: dict, requirement: str) -> dict:
    validation_warning = _validate_crewai_response(result)
    if validation_warning:
        return _safe_crewai_revision_response(result, requirement, validation_warning)

    story = result.get("story")
    context = result.get("context") or {}
    route = route_requirement(requirement)
    context["route"] = route
    if isinstance(story, dict):
        story.setdefault("requirement", requirement)
        story.setdefault("story_type", route.get("story_type") or story.get("story_type", "software_feature"))
        story["route"] = route
    post_validation = validate_post_generation(requirement, story, context, route)
    evaluation = result.get("evaluation") or {}
    if not post_validation["passed"]:
        story = post_validation["normalized_story"] or story
        result["story"] = story
        result["context"] = context
        warning = "CrewAI story failed deterministic post-generation validation."
        issues = list(dict.fromkeys(evaluation.get("issues", []) + post_validation["issues"] + [warning]))
        evaluation = {
            "status": "REVISION",
            "issues": issues,
            "revision_instructions": list(dict.fromkeys(evaluation.get("revision_instructions", []) + post_validation["issues"])),
            "dod_score": evaluation.get("dod_score", {}),
            "warnings": list(dict.fromkeys(evaluation.get("warnings", []) + post_validation.get("warnings", []) + [warning])),
        }
        result["evaluation"] = evaluation
        result["actions"] = blocked_actions()
        result.setdefault("next_steps", [])
        return result

    finalized = finalize_generation(story, evaluation)
    result["evaluation"] = finalized["evaluation"]
    if not finalized["actions_ready"]:
        result["actions"] = finalized["actions"]
    else:
        result["actions"] = {
            "jira": JiraTool().prepare_action(story),
            "slack": SlackTool().prepare_action(story, result["evaluation"]),
        }
    result.setdefault("next_steps", [])
    return result


def _validate_crewai_response(result: dict) -> str | None:
    try:
        ResearchContextOutput.model_validate(result.get("context") or {})
        PlannerStoryOutput.model_validate(result.get("story") or {})
        EvaluationOutput.model_validate(result.get("evaluation") or {})
    except Exception as exc:
        return f"CrewAI structured output failed validation; output requires revision. Reason: {exc}"
    return None


def _safe_crewai_revision_response(result: dict, requirement: str, warning: str) -> dict:
    context = dump_model(ResearchContextOutput.model_validate(result.get("context") or {}))
    return {
        "context": context,
        "story": {
            "title": requirement.strip(),
            "requirement": requirement,
            "story_type": "software_feature",
            "user_story": "",
            "acceptance_criteria": [],
            "story_points": None,
            "tasks": {"be": [], "fe": [], "qa": []},
            "definition_of_done": [],
            "planning_status": "REVISION",
            "clarification_questions": [],
            "assumptions": [],
            "story_splits": [],
            "sprint_allocation": [],
            "context_sources": [],
            "context_quality": {},
            "planner_quality": {"passed": False, "failures": [warning]},
            "route": {},
            "warnings": [warning],
        },
        "evaluation": {
            "status": "REVISION",
            "issues": [warning],
            "revision_instructions": [warning],
            "dod_score": {},
            "warnings": [warning],
        },
        "actions": blocked_actions(),
        "next_steps": ["Review CrewAI structured output and rerun after fixing invalid fields."],
    }


def _mark_crewai_failure_for_revision(result: dict, warning: str) -> dict:
    evaluation = dict(result.get("evaluation") or {})
    issues = list(dict.fromkeys(evaluation.get("issues", []) + [warning]))
    evaluation.update(
        {
            "status": "REVISION",
            "issues": issues,
            "revision_instructions": list(dict.fromkeys(evaluation.get("revision_instructions", []) + [warning])),
            "warnings": list(dict.fromkeys(evaluation.get("warnings", []) + [warning])),
        }
    )
    result["evaluation"] = evaluation
    result["actions"] = blocked_actions()
    story = result.get("story")
    if isinstance(story, dict) and story.get("planning_status") == "READY":
        story["planning_status"] = "REVISION"
    return result


class ScrumMasterCrew:
    def __init__(self) -> None:
        profiles = get_runtime_profiles()
        self.task_profiles = profiles.tasks
        self.researcher = ResearcherAgent(
            profile=profiles.agents.get("researcher"),
            task_profile=profiles.tasks.get("research_task"),
        )
        self.planner = PlannerAgent(
            profile=profiles.agents.get("planner"),
            task_profile=profiles.tasks.get("planning_task"),
        )
        self.evaluator = EvaluatorAgent(
            profile=profiles.agents.get("evaluator"),
            task_profile=profiles.tasks.get("evaluation_task"),
        )
    def run(self, requirement: str, n_results: int = 5, allow_fallback_without_context: bool = False, forced_context_docs: list[str] | None = None, progress_callback: Callable[[str, dict], None] | None = None, project_id: str | None = None) -> dict:
        self.jira_tool = JiraTool.from_project(project_id)
        self.slack_tool = SlackTool.from_project(project_id)
        route = route_requirement(requirement)
        requirement_type = route.get("story_type") or classify_requirement(requirement)
        logger.info(
            "Pipeline started requirement_length=%s n_results=%s allow_fallback_without_context=%s requirement_type=%s route_domain=%s project_id=%s",
            len(requirement),
            n_results,
            allow_fallback_without_context,
            requirement_type,
            route.get("domain"),
            project_id,
        )
        logger.info("Researcher stage started")
        context = self._run_researcher(requirement=requirement, n_results=n_results, route=route, forced_context_docs=forced_context_docs, project_id=project_id)
        context["route"] = route
        logger.info(
            "Researcher stage completed documents=%s raw_matches=%s confidence=%s warnings=%s retrieval_status=%s",
            len(context.get("documents", [])),
            context.get("raw_match_count", len(context.get("matches", []))),
            context.get("confidence"),
            len(context.get("warnings", [])),
            context.get("retrieval_status"),
        )

        context = self._select_context_for_requirement(requirement, context, route)
        if progress_callback:
            progress_callback("planner", {"context": context})

        if should_block_planning(context, allow_fallback_without_context):
            return self._context_required_response(context, route)
        if context.get("retrieval_status") in {"empty", "no_relevant_context", "failed"} and allow_fallback_without_context:
            context.setdefault("warnings", []).append(
                "Fallback planning was user-approved even though no relevant retrieved context met the threshold."
            )

        planner_context = dict(context)
        logger.info("Planner stage started")
        story = self._run_planner(
            requirement=requirement,
            context=planner_context,
            requirement_type=requirement_type,
            route=route,
        )
        story["requirement"] = requirement
        story["story_type"] = requirement_type
        story["route"] = route
        story["context_quality"] = {
            "retrieval_status": planner_context.get("retrieval_status"),
            "confidence": planner_context.get("confidence"),
            "source_count": len(planner_context.get("retrieved_sources", [])),
            "research_quality_gate": planner_context.get("quality_gate", {}),
        }
        planner_quality = evaluate_planner_output(requirement, story, planner_context)
        story["planner_quality"] = planner_quality
        post_validation = validate_post_generation(requirement, story, planner_context, route)
        if post_validation.get("warnings"):
            story["warnings"] = list(dict.fromkeys(story.get("warnings", []) + post_validation["warnings"]))
        if not post_validation["passed"]:
            story = post_validation["normalized_story"] or story
            planner_quality = evaluate_planner_output(requirement, story, planner_context)
            planner_quality["passed"] = False
            planner_quality["failures"] = list(dict.fromkeys(planner_quality.get("failures", []) + post_validation["issues"]))
            story["planner_quality"] = planner_quality
        logger.info(
            "Planner stage completed title=%s planning_status=%s warnings=%s quality_passed=%s quality_failures=%s",
            story.get("title"),
            story.get("planning_status", "READY"),
            len(story.get("warnings", [])),
            planner_quality.get("passed"),
            len(planner_quality.get("failures", [])),
        )

        if not planner_quality["passed"]:
            evaluation = self._planner_quality_failed_response(planner_quality)
            evaluation = self._apply_runtime_safety_issues(story, evaluation, planner_context)
            evaluation = self._apply_post_generation_validation(requirement, story, evaluation, requirement_type)
            story["planner_quality"] = evaluate_planner_output(requirement, story, planner_context)
            if story.get("planning_status") == "REVISION":
                story["planner_quality"]["passed"] = False
            actions = self._prepare_actions(story, evaluation)
            logger.info("Evaluator stage blocked because planner quality gate failed")
            return {
                "context": context,
                "story": story,
                "evaluation": evaluation,
                "actions": actions,
            }

        if progress_callback:
            progress_callback("evaluator", {"story": story})

        logger.info("Evaluator stage started")
        evaluation = self.evaluator.run(story=story)
        evaluation = self._apply_runtime_safety_issues(story, evaluation, planner_context)
        evaluation = self._apply_post_generation_validation(requirement, story, evaluation, requirement_type)
        evaluation = finalize_generation(story, evaluation)["evaluation"]
        story["planner_quality"] = evaluate_planner_output(requirement, story, planner_context)
        if story.get("planning_status") == "REVISION":
            story["planner_quality"]["passed"] = False
        logger.info(
            "Evaluator stage completed status=%s issues=%s warnings=%s",
            evaluation.get("status"),
            len(evaluation.get("issues", [])),
            len(evaluation.get("warnings", [])),
        )

        actions = self._prepare_actions(story, evaluation)
        logger.info("Pipeline completed action_ready jira=%s slack=%s", actions["jira"]["ready"], actions["slack"]["ready"])
        return {
            "context": context,
            "story": story,
            "evaluation": evaluation,
            "actions": actions,
        }

    def _run_researcher(self, requirement: str, n_results: int, route: dict, forced_context_docs: list[str] | None = None, project_id: str | None = None) -> dict:
        try:
            return self.researcher.run(requirement=requirement, n_results=n_results, route=route, forced_context_docs=forced_context_docs, project_id=project_id)
        except TypeError as exc:
            if "route" not in str(exc) and "project_id" not in str(exc):
                raise
            return self.researcher.run(requirement=requirement, n_results=n_results)

    def _run_planner(self, requirement: str, context: dict, requirement_type: str, route: dict) -> dict:
        try:
            return self.planner.run(
                requirement=requirement,
                context=context,
                requirement_type=requirement_type,
                route=route,
            )
        except TypeError as exc:
            if "route" not in str(exc):
                raise
            return self.planner.run(
                requirement=requirement,
                context=context,
                requirement_type=requirement_type,
            )

    def _apply_runtime_safety_issues(self, story: dict, evaluation: dict, context: dict) -> dict:
        issues = []
        if story.get("fallback_used"):
            issues.append("Planner fallback was used; human revision is required before downstream actions.")
        if context.get("confidence", 1.0) < 0.5:
            issues.append("Retrieved context confidence is low; human revision is required before downstream actions.")
        if not issues:
            return evaluation

        return {
            "status": "REVISION",
            "issues": list(dict.fromkeys(evaluation.get("issues", []) + issues)),
            "revision_instructions": list(dict.fromkeys(evaluation.get("revision_instructions", []) + issues)),
            "dod_score": evaluation.get("dod_score", {}),
            "warnings": evaluation.get("warnings", []),
        }

    def _apply_post_generation_validation(
        self,
        requirement: str,
        story: dict,
        evaluation: dict,
        requirement_type: str,
    ) -> dict:
        validation_issues = validate_story_against_requirement(requirement, story)
        if not validation_issues:
            return evaluation

        logger.info("Post-generation validation failed issues=%s", len(validation_issues))
        if requirement_type == OVERSIZED_REQUEST:
            story["planning_status"] = "SPLIT_RECOMMENDED"
        elif requirement_type == AMBIGUOUS_REQUEST:
            story["planning_status"] = "NEEDS_CLARIFICATION"
        else:
            story["planning_status"] = "REVISION"

        issues = list(dict.fromkeys(evaluation.get("issues", []) + validation_issues))
        return {
            "status": "REVISION",
            "issues": issues,
            "revision_instructions": list(dict.fromkeys(evaluation.get("revision_instructions", []) + validation_issues)),
            "dod_score": evaluation.get("dod_score", {}),
            "warnings": evaluation.get("warnings", []),
        }

    def _select_context_for_requirement(self, requirement: str, context: dict, route: dict) -> dict:
        selected = select_context_for_route(requirement, context, route)
        selected["ignored_context_sources"] = self._compact_ignored_sources(selected.get("ignored_context_sources", []))
        return selected

    def _compact_ignored_sources(self, ignored_sources: list[dict]) -> list[dict]:
        return [
            {
                "id": source.get("id", ""),
                "source": source.get("source", "unknown source"),
                "chunk_index": source.get("chunk_index", "?"),
                "score": source.get("score", 0.0),
                "ignored_reason": "unrelated_to_requirement_domain",
            }
            for source in ignored_sources
        ]

    def _context_required_response(self, context: dict, route: dict) -> dict:
        logger.info("Planner stage blocked because no relevant context met retrieval requirements")
        if context.get("missing_required_sources"):
            warning = f"Planner blocked because required context source(s) are missing: {', '.join(context['missing_required_sources'])}."
        else:
            warning = "Planner blocked because no relevant retrieved context met the configured threshold."
        context["route"] = route
        return {
            "context": context,
            "story": None,
            "evaluation": {
                "status": "NEEDS_CONTEXT",
                "issues": [warning],
                "revision_instructions": [
                    "Import or ingest more relevant documentation, then rerun the requirement.",
                    "Or rerun with allow_fallback_without_context=true to generate a clearly marked fallback story.",
                ],
                "warnings": context.get("warnings", []) + [warning],
            },
            "actions": {
                "jira": {"ready": False, "payload": None, "warnings": [warning]},
                "slack": {"ready": False, "payload": None, "warnings": [warning]},
            },
            "next_steps": [
                "Import or ingest documentation that describes this requirement.",
                "Rerun the same requirement after ingestion.",
                "If you intentionally want generic fallback output, set allow_fallback_without_context=true.",
            ],
        }

    def _planner_quality_failed_response(self, planner_quality: dict) -> dict:
        warning = "Planner quality gate failed; evaluator was not run because the story is not ready for evaluation."
        issues = list(dict.fromkeys(planner_quality.get("failures", []) + [warning]))
        return {
            "status": "REVISION",
            "issues": issues,
            "revision_instructions": issues,
            "dod_score": {},
            "warnings": [warning],
        }

    def _prepare_actions(self, story: dict, evaluation: dict) -> dict:
        if evaluation.get("status") != "APPROVED" or story.get("planning_status", "READY") != "READY":
            logger.info(
                "Action previews blocked evaluation_status=%s planning_status=%s",
                evaluation.get("status"),
                story.get("planning_status", "READY"),
            )
            return blocked_actions()

        logger.info("Action previews prepared for approved ready story")
        return {
            "jira": self.jira_tool.prepare_action(story),
            "slack": self.slack_tool.prepare_action(story, evaluation),
        }
