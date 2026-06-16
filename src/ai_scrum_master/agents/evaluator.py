from __future__ import annotations

import json
import re
from typing import Any

from ai_scrum_master.core.schemas.agent_schemas import EvaluationOutput, dump_model
from ai_scrum_master.core.config.settings import AgentProfileConfig, TaskProfileConfig
from ai_scrum_master.core.llm.json_utils import normalize_llm_json_output
from ai_scrum_master.core.llm.setup import build_llm
from ai_scrum_master.core.utils.logging import get_logger
from ai_scrum_master.core.llm.prompts import render_prompt
from ai_scrum_master.core.validation.quality import (
    FIBONACCI_POINTS,
    domain_contamination_issues,
    is_generic_acceptance_criterion,
    is_given_when_then_ordered,
    is_placeholder_task,
    is_user_story_task,
    validate_story_against_requirement,
)

READY = "READY"
NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
SPLIT_RECOMMENDED = "SPLIT_RECOMMENDED"
NEEDS_SPLIT = "NEEDS_SPLIT"

logger = get_logger(__name__)


class EvaluatorAgent:
    def __init__(
        self,
        llm: Any | None = None,
        use_llm: bool = True,
        profile: AgentProfileConfig | None = None,
        task_profile: TaskProfileConfig | None = None,
    ) -> None:
        self.llm = llm
        self.use_llm = use_llm
        self.profile = profile
        self.task_profile = task_profile

    def run(self, story: dict) -> dict:
        logger.info("Evaluator started planning_status=%s", story.get("planning_status", READY))
        rule_result = self._rule_evaluate(story)
        logger.info(
            "Evaluator rule check completed status=%s issues=%s",
            rule_result["status"],
            len(rule_result["issues"]),
        )
        if story.get("route", {}).get("domain") == "benchmark_case":
            logger.info("Evaluator returning rule result directly for benchmark case (LLM bypassed)")
            return rule_result
        if story.get("planning_status", READY) != READY:
            logger.info("Evaluator returning rule result because planning_status is non-ready")
            return rule_result
        if not self.use_llm:
            logger.info("Evaluator returning rule result because LLM is disabled")
            return rule_result

        try:
            llm = self.llm or build_llm()
            messages = self._build_messages(story, rule_result)
            logger.info(
                "LLM trace evaluator request messages=%s prompt_chars=%s rule_status=%s dod_score=%s/%s",
                len(messages),
                sum(len(message["content"]) for message in messages),
                rule_result["status"],
                rule_result.get("dod_score", {}).get("passed"),
                rule_result.get("dod_score", {}).get("total"),
            )
            raw_output = llm.call(messages)
            logger.info("LLM trace evaluator response raw_chars=%s", len(str(raw_output)))
            result = self._parse_result(raw_output)
            logger.info("LLM trace evaluator parsed keys=%s", sorted(result.keys()))
            return self._normalize_result(result, rule_result)
        except Exception as exc:
            logger.exception("Evaluator failed to use LLM output; using rule fallback")
            rule_result["warnings"].append(f"Evaluator LLM unavailable; used rule fallback. Reason: {exc}")
            return self._validate_output(rule_result)

    def _build_messages(self, story: dict, rule_result: dict) -> list[dict[str, str]]:
        return [
            {"role": "user", "content": self._build_prompt(story, rule_result)},
        ]

    def _build_prompt(self, story: dict, rule_result: dict) -> str:
        role = self.profile.role if self.profile else "Evaluator Agent"
        goal = self.profile.goal if self.profile else "Evaluate whether this story is ready for Jira creation."
        backstory = self.profile.backstory if self.profile else "You enforce quality gates for an AI Scrum Master system."
        task_description = (
            self.task_profile.description
            if self.task_profile
            else "Evaluate story quality, domain isolation, context grounding, and readiness against mandatory Scrum and formatting rules."
        )
        expected_output = (
            self.task_profile.expected_output
            if self.task_profile
            else "JSON result containing status APPROVED or REVISION with concrete issues, revision instructions, and warnings."
        )
        return render_prompt(
            "evaluator.md",
            role=role,
            goal=goal,
            backstory=backstory,
            task_description=task_description,
            expected_output=expected_output,
            rule_result_json=json.dumps(rule_result, ensure_ascii=False, indent=2),
            requirement=story.get("requirement", story.get("title", "")),
            story_output=json.dumps(story, ensure_ascii=False, indent=2),
            retrieved_context=json.dumps(story.get("context_sources", []), ensure_ascii=False, indent=2),
        )

    def _parse_result(self, raw_output: Any) -> dict:
        if isinstance(raw_output, dict):
            return raw_output

        text = normalize_llm_json_output(raw_output)
        
        # Remove <think>...</think> blocks if present
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        
        return json.loads(text)

    def _normalize_result(self, result: dict, rule_result: dict) -> dict:
        status = result.get("status")
        if status not in {"APPROVED", "REVISION"}:
            status = rule_result["status"]

        issues = self._string_list(result.get("issues", []))
        revision_instructions = self._string_list(result.get("revision_instructions", []))
        warnings_from_llm = self._string_list(result.get("warnings", []))
        warnings = list(dict.fromkeys(rule_result.get("warnings", []) + warnings_from_llm))
        dod_score = rule_result.get("dod_score", {})

        if rule_result["status"] == "REVISION":
            status = "REVISION"
            issues = list(dict.fromkeys(rule_result["issues"] + issues))
            revision_instructions = list(
                dict.fromkeys(rule_result["revision_instructions"] + revision_instructions)
            )
        else:
            status = "APPROVED"
            if issues:
                warnings = list(dict.fromkeys(
                    warnings
                    + [
                        "Evaluator LLM returned revision issues after deterministic rules approved; ignored LLM-only issues to avoid unsupported false positives."
                    ]
                    + [f"Ignored evaluator LLM issue: {issue}" for issue in issues]
                ))
            issues = []
            revision_instructions = []

        return self._validate_output({
            "status": status,
            "issues": issues,
            "revision_instructions": revision_instructions,
            "dod_score": dod_score,
            "warnings": warnings,
        })

    def _string_list(self, values: Any) -> list[str]:
        if not isinstance(values, list):
            return []
        normalized = []
        for value in values:
            if isinstance(value, str):
                normalized.append(value)
            elif value not in (None, "", []):
                normalized.append(json.dumps(value, ensure_ascii=False))
        return normalized

    def _rule_evaluate(self, story: dict) -> dict:
        issues: list[str] = []
        warnings: list[str] = []
        dod_score: dict[str, Any] = {}
        issues.extend(validate_story_against_requirement(story.get("requirement", story.get("title", "")), story))

        story_type = story.get("story_type", "software_feature")
        issues.extend(domain_contamination_issues(story.get("requirement", story.get("title", "")), story))
        planning_status = story.get("planning_status", READY)

        if planning_status == READY:
            user_story = story.get("user_story", "")
            if "As a" not in user_story or "I want" not in user_story or "so that" not in user_story.lower():
                issues.append("User story must follow As a / I want / So that format.")

            acceptance_criteria = story.get("acceptance_criteria", [])
            if len(acceptance_criteria) < 3:
                issues.append("At least 3 acceptance criteria are required.")
            for index, criterion in enumerate(acceptance_criteria, start=1):
                if not is_given_when_then_ordered(criterion):
                    issues.append(f"Acceptance criterion #{index} must use Given / When / Then.")
                if is_generic_acceptance_criterion(criterion):
                    issues.append(f"Acceptance criterion #{index} is generic template text and must be business-specific.")

            if story.get("story_points") not in FIBONACCI_POINTS:
                issues.append("Story points must use Fibonacci values.")

            tasks = story.get("tasks", {})
            for key in ("be", "fe", "qa"):
                if key not in tasks:
                    issues.append(f"Tasks must include {key.upper()} group.")
                elif not self._has_actionable_tasks(tasks.get(key)):
                    issues.append(f"Tasks must include at least one actionable {key.upper()} item.")
                for item in tasks.get(key, []) if isinstance(tasks.get(key), list) else []:
                    if is_user_story_task(item):
                        issues.append(f"Tasks must be concrete actions, not user stories: {key.upper()} item '{item}'.")

            definition_of_done = story.get("definition_of_done")
            if not definition_of_done:
                issues.append("Definition of done is required.")
            else:
                dod_score = self._score_definition_of_done(definition_of_done, story, story_type)
                if len(dod_score.get("checks", [])) < 4:
                    issues.append("Definition of done must include at least 4 detailed completion checks.")
                if dod_score["passed"] < dod_score["minimum_passed"]:
                    issues.append(
                        f"Definition of Done score {dod_score['passed']}/{dod_score['total']} is below minimum {dod_score['minimum_passed']}."
                    )
                if any(
                    dimension["name"] == "no_software_delivery_template" and not dimension["passed"]
                    for dimension in dod_score.get("dimensions", [])
                ):
                    issues.append("Process-improvement DoD must not use software delivery template checks.")
        elif planning_status == NEEDS_CLARIFICATION:
            if len(story.get("clarification_questions", [])) < 3:
                issues.append("Clarification-needed stories must include at least 3 clarification questions.")
            if self._has_ready_story_fields(story):
                issues.append("Clarification-needed stories must not include story points, acceptance criteria, tasks, or Definition of Done.")
            warnings = ["Requirement needs clarification before Jira-ready planning."]
        elif planning_status in {NEEDS_SPLIT, SPLIT_RECOMMENDED}:
            if not story.get("story_splits"):
                issues.append("Oversized requests must include story_splits.")
            if not story.get("sprint_allocation"):
                issues.append("Oversized requests must include sprint_allocation.")
            warnings = ["Oversized requests must be split into sprint-ready stories before Jira creation."]
        elif planning_status != READY:
            issues.append("planning_status must be READY, NEEDS_CLARIFICATION, NEEDS_SPLIT, or SPLIT_RECOMMENDED.")
            warnings = []
        else:
            warnings = []

        status = "REVISION" if issues else "APPROVED"
        return self._validate_output({
            "status": status,
            "issues": issues,
            "revision_instructions": issues,
            "dod_score": dod_score,
            "warnings": warnings,
        })

    def _has_ready_story_fields(self, story: dict) -> bool:
        tasks = story.get("tasks", {})
        return (
            bool(story.get("user_story"))
            or bool(story.get("acceptance_criteria"))
            or story.get("story_points") is not None
            or bool(story.get("definition_of_done"))
            or any(tasks.get(group) for group in ("be", "fe", "qa") if isinstance(tasks, dict))
        )

    def _has_actionable_tasks(self, value: Any) -> bool:
        if not isinstance(value, list):
            return False
        return any(
            isinstance(item, str)
            and len(item.strip().split()) >= 3
            and not is_user_story_task(item)
            and not is_placeholder_task(item)
            for item in value
        )

    def _score_definition_of_done(self, items: Any, story: dict, story_type: str = "software_feature") -> dict[str, Any]:
        if not isinstance(items, list):
            return {
                "passed": 0,
                "total": 5,
                "minimum_passed": 4,
                "ratio": 0.0,
                "checks": [],
                "dimensions": [
                    {"name": "list_format", "passed": False},
                ],
            }
        checks = [item.strip() for item in items if isinstance(item, str) and item.strip()]
        text = " ".join(checks).lower()
        if story_type == "process_improvement":
            dimensions = [
                ("sprint_goal_or_outcome", any(term in text for term in ("sprint goal", "goal", "outcome"))),
                ("backlog_or_scope_alignment", any(term in text for term in ("product backlog", "backlog", "selected", "scope"))),
                ("team_alignment", any(term in text for term in ("scrum team", "team", "alignment", "agreed"))),
                ("validation_or_feedback", any(term in text for term in ("checklist", "template", "adoption", "validation", "feedback"))),
                ("no_software_delivery_template", not any(self._is_software_template_dod(item) for item in checks)),
            ]
        else:
            dimensions = [
                ("acceptance_validation", "acceptance" in text and "criteria" in text),
                ("implementation_completion", any(term in text for term in ("implementation", "implemented", "task", "backend", "frontend", "api", "ui", "be", "fe"))),
                ("qa_testing_evidence", any(term in text for term in ("test", "testing", "qa", "validation", "validated"))),
                ("story_specific_completion", self._has_story_specific_dod_terms(story, text)),
                ("no_generic_or_wrong_domain", not domain_contamination_issues(story.get("requirement", story.get("title", "")), {"definition_of_done": checks})),
            ]
        passed = sum(1 for _name, ok in dimensions if ok)
        total = len(dimensions)
        minimum_passed = 4 if total >= 5 else max(1, total)
        return {
            "passed": passed,
            "total": total,
            "minimum_passed": minimum_passed,
            "ratio": round(passed / total, 2) if total else 0.0,
            "checks": checks,
            "dimensions": [{"name": name, "passed": ok} for name, ok in dimensions],
        }

    def _has_story_specific_dod_terms(self, story: dict, dod_text: str) -> bool:
        source_text = " ".join(
            [
                str(story.get("title", "")),
                str(story.get("user_story", "")),
                " ".join(story.get("acceptance_criteria", [])),
                " ".join(story.get("tasks", {}).get("be", [])),
                " ".join(story.get("tasks", {}).get("fe", [])),
                " ".join(story.get("tasks", {}).get("qa", [])),
            ]
        ).lower()
        stopwords = {
            "acceptance", "criteria", "given", "when", "then", "user", "story", "task", "tasks",
            "implementation", "testing", "validation", "complete", "completed", "system",
        }
        terms = {
            token
            for token in re.findall(r"[a-z0-9]+", source_text)
            if len(token) >= 4 and token not in stopwords
        }
        return any(term in dod_text for term in terms)

    def _is_software_template_dod(self, item: str) -> bool:
        lowered = item.lower()
        software_phrases = (
            "be and fe implementation",
            "backend",
            "frontend",
            "integrated without known blockers",
            "jira creation",
            "demo-ready",
        )
        return any(phrase in lowered for phrase in software_phrases)

    def _validate_output(self, payload: dict) -> dict:
        return dump_model(EvaluationOutput.model_validate(payload))
