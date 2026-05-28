from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_scrum_master.agents.evaluator import EvaluatorAgent
from ai_scrum_master.agents.crewai_contract import build_crewai_task
from ai_scrum_master.agents.planner import PlannerAgent
from ai_scrum_master.agents.researcher import ResearcherAgent
from ai_scrum_master.core.agent_schemas import EvaluationOutput, PlannerStoryOutput, ResearchContextOutput
from ai_scrum_master.core.config import get_runtime_profiles


@dataclass(frozen=True)
class CrewSpec:
    agents: list[Any]
    tasks: list[Any]
    process: Any
    verbose: bool = True


class ScrumMasterTasks:
    def __init__(self, task_profiles: dict | None = None) -> None:
        self.task_profiles = task_profiles or {}

    def research_task(self, agent: Any, requirement: str, n_results: int = 5) -> Any:
        profile = self.task_profiles.get("research_task")
        expected_output = (
            profile.expected_output
            if profile
            else "Context bundle with documents, source snippets, planning_brief, confidence score, and retrieval warnings."
        )
        description = f"""
            Retrieve documentation context for the current requirement and prepare a ranked evidence pack.

            The agent must search only the configured project context collection, keep confidence and source metadata,
            and return a planning brief that the Planner can use without relying on memory or previous requests.

            Current requirement: {requirement}
            Number of requested results: {n_results}
        """
        return build_crewai_task(
            description=description,
            agent=agent,
            expected_output=expected_output,
            output_pydantic=ResearchContextOutput,
        )

    def planning_task(
        self,
        agent: Any,
        requirement: str,
        context: dict,
        planning_status: str,
        task_context: list[Any] | None = None,
    ) -> Any:
        profile = self.task_profiles.get("planning_task")
        expected_output = (
            profile.expected_output
            if profile
            else "JSON story with title, user_story, acceptance_criteria, story_points, tasks, definition_of_done, assumptions, context_sources, and planning_status."
        )
        description = f"""
            Convert the current requirement and selected retrieved context into one sprint-planning decision.

            The Planner must derive business context from docs first, write business-specific acceptance criteria,
            split oversized work, ask clarification questions for ambiguous requests, and cite only selected context sources.

            Current requirement: {requirement}
            Planning status from local rules: {planning_status}
            Retrieval status: {context.get("retrieval_status", "unknown")}
            Context confidence: {context.get("confidence", 0.0)}
            Selected source count: {len(context.get("retrieved_sources", []))}
        """
        return build_crewai_task(
            description=description,
            agent=agent,
            expected_output=expected_output,
            context=task_context,
            output_pydantic=PlannerStoryOutput,
        )

    def evaluation_task(self, agent: Any, story: dict, task_context: list[Any] | None = None) -> Any:
        profile = self.task_profiles.get("evaluation_task")
        expected_output = (
            profile.expected_output
            if profile
            else "JSON result containing status APPROVED or REVISION with concrete issues, revision instructions, and warnings."
        )
        description = f"""
            Evaluate the Planner output against Scrum story quality, local validation rules, context grounding,
            domain isolation, and Jira/Slack readiness gates.

            The Evaluator must preserve deterministic rule failures, reject unrelated-domain contamination,
            and approve only READY stories that are safe for downstream action previews.

            Story title: {story.get("title", "")}
            Planning status: {story.get("planning_status", "READY")}
            Story type: {story.get("story_type", "software_feature")}
        """
        return build_crewai_task(
            description=description,
            agent=agent,
            expected_output=expected_output,
            context=task_context,
            output_pydantic=EvaluationOutput,
        )


def build_scrum_master_crew(requirement: str, n_results: int = 5, verbose: bool = True) -> Any:
    profiles = get_runtime_profiles()
    researcher = ResearcherAgent(
        profile=profiles.agents.get("researcher"),
        task_profile=profiles.tasks.get("research_task"),
    )
    planner = PlannerAgent(
        profile=profiles.agents.get("planner"),
        task_profile=profiles.tasks.get("planning_task"),
    )
    evaluator = EvaluatorAgent(
        profile=profiles.agents.get("evaluator"),
        task_profile=profiles.tasks.get("evaluation_task"),
    )

    researcher_agent = researcher.create_agent()
    planner_agent = planner.create_agent()
    evaluator_agent = evaluator.create_agent()

    task_builder = ScrumMasterTasks(profiles.tasks)
    pending_context = {"retrieval_status": "pending", "confidence": 0.0, "retrieved_sources": []}
    pending_story = {"title": "pending", "planning_status": "pending", "story_type": "pending"}
    agents = [researcher_agent, planner_agent, evaluator_agent]
    research_task = task_builder.research_task(researcher_agent, requirement, n_results)
    planning_task = task_builder.planning_task(
        planner_agent,
        requirement,
        pending_context,
        "pending",
        task_context=[research_task],
    )
    evaluation_task = task_builder.evaluation_task(
        evaluator_agent,
        pending_story,
        task_context=[research_task, planning_task],
    )
    tasks = [research_task, planning_task, evaluation_task]
    process = _sequential_process()

    try:
        from crewai import Crew
    except Exception:
        return CrewSpec(agents=agents, tasks=tasks, process=process, verbose=verbose)

    try:
        return Crew(agents=agents, tasks=tasks, process=process, verbose=verbose)
    except Exception:
        return CrewSpec(agents=agents, tasks=tasks, process=process, verbose=verbose)


def _sequential_process() -> Any:
    try:
        from crewai import Process
    except Exception:
        return "sequential"
    return Process.sequential
