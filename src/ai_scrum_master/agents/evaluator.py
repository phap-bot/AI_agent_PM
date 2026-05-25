from __future__ import annotations

import json
import re
from typing import Any

from ai_scrum_master.core.config import AgentProfileConfig
from ai_scrum_master.core.llm_setup import build_llm
from ai_scrum_master.core.logging import get_logger

FIBONACCI_POINTS = {1, 2, 3, 5, 8, 13}
READY = "READY"
NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
SPLIT_RECOMMENDED = "SPLIT_RECOMMENDED"

logger = get_logger(__name__)


class EvaluatorAgent:
    def __init__(
        self,
        llm: Any | None = None,
        use_llm: bool = True,
        profile: AgentProfileConfig | None = None,
    ) -> None:
        self.llm = llm
        self.use_llm = use_llm
        self.profile = profile

    def run(self, story: dict) -> dict:
        logger.info("Evaluator started planning_status=%s", story.get("planning_status", READY))
        rule_result = self._rule_evaluate(story)
        logger.info(
            "Evaluator rule check completed status=%s issues=%s",
            rule_result["status"],
            len(rule_result["issues"]),
        )
        if not self.use_llm:
            logger.info("Evaluator returning rule result because LLM is disabled")
            return rule_result

        try:
            llm = self.llm or build_llm()
            logger.info("Evaluator LLM call started")
            raw_output = llm.call(self._build_prompt(story, rule_result))
            logger.info("Evaluator LLM call completed")
            result = self._parse_result(raw_output)
            logger.info("Evaluator parsed LLM JSON successfully")
            return self._normalize_result(result, rule_result)
        except Exception as exc:
            logger.exception("Evaluator failed to use LLM output; using rule fallback")
            rule_result["warnings"].append(f"Evaluator LLM unavailable; used rule fallback. Reason: {exc}")
            return rule_result

    def _build_prompt(self, story: dict, rule_result: dict) -> str:
        role = self.profile.role if self.profile else "Evaluator Agent"
        goal = self.profile.goal if self.profile else "Evaluate whether this story is ready for Jira creation."
        backstory = self.profile.backstory if self.profile else "You enforce quality gates for an AI Scrum Master system."
        return f"""
You are {role}.
Goal: {goal}
Backstory: {backstory}

Evaluate whether this story is ready for Jira creation.

Story JSON:
{json.dumps(story, ensure_ascii=False, indent=2)}

Rule-based pre-check:
{json.dumps(rule_result, ensure_ascii=False, indent=2)}

Return only valid JSON with this exact shape:
{{
  "status": "APPROVED",
  "issues": [],
  "revision_instructions": [],
  "warnings": []
}}

Rules:
- status must be either APPROVED or REVISION.
- Require As a / I want / so that story format.
- Require at least 3 Given / When / Then acceptance criteria.
- Require Fibonacci story points: 1, 2, 3, 5, 8, 13.
- Require BE, FE, and QA task groups.
- Do not approve if rule-based pre-check found blocking issues.
""".strip()

    def _parse_result(self, raw_output: Any) -> dict:
        if isinstance(raw_output, dict):
            return raw_output

        text = str(raw_output).strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Evaluator LLM did not return JSON.")
        return json.loads(text[start : end + 1])

    def _normalize_result(self, result: dict, rule_result: dict) -> dict:
        status = result.get("status")
        if status not in {"APPROVED", "REVISION"}:
            status = rule_result["status"]

        issues = list(result.get("issues", []))
        revision_instructions = list(result.get("revision_instructions", []))
        warnings = list(result.get("warnings", []))

        if rule_result["status"] == "REVISION":
            status = "REVISION"
            issues = list(dict.fromkeys(rule_result["issues"] + issues))
            revision_instructions = list(
                dict.fromkeys(rule_result["revision_instructions"] + revision_instructions)
            )

        return {
            "status": status,
            "issues": issues,
            "revision_instructions": revision_instructions,
            "warnings": warnings,
        }

    def _rule_evaluate(self, story: dict) -> dict:
        issues: list[str] = []

        user_story = story.get("user_story", "")
        if "As a" not in user_story or "I want" not in user_story or "so that" not in user_story.lower():
            issues.append("User story must follow As a / I want / So that format.")

        acceptance_criteria = story.get("acceptance_criteria", [])
        if len(acceptance_criteria) < 3:
            issues.append("At least 3 acceptance criteria are required.")
        for index, criterion in enumerate(acceptance_criteria, start=1):
            if not self._is_given_when_then(criterion):
                issues.append(f"Acceptance criterion #{index} must use Given / When / Then.")

        if story.get("story_points") not in FIBONACCI_POINTS:
            issues.append("Story points must use Fibonacci values.")

        tasks = story.get("tasks", {})
        for key in ("be", "fe", "qa"):
            if key not in tasks:
                issues.append(f"Tasks must include {key.upper()} group.")

        if not story.get("definition_of_done"):
            issues.append("Definition of done is required.")

        planning_status = story.get("planning_status", READY)
        if planning_status == NEEDS_CLARIFICATION:
            if not story.get("clarification_questions"):
                issues.append("Clarification-needed stories must include clarification questions.")
            issues.append("Requirement needs clarification before Jira-ready planning.")
        elif planning_status == SPLIT_RECOMMENDED:
            if not story.get("story_splits"):
                issues.append("Oversized requests must include story_splits.")
            if not story.get("sprint_allocation"):
                issues.append("Oversized requests must include sprint_allocation.")
            issues.append("Oversized requests must be split into sprint-ready stories before Jira creation.")
        elif planning_status != READY:
            issues.append("planning_status must be READY, NEEDS_CLARIFICATION, or SPLIT_RECOMMENDED.")

        status = "REVISION" if issues else "APPROVED"
        return {
            "status": status,
            "issues": issues,
            "revision_instructions": issues,
            "warnings": [],
        }

    def _is_given_when_then(self, criterion: str) -> bool:
        return all(re.search(rf"\b{token}\b", criterion, flags=re.IGNORECASE) for token in ("given", "when", "then"))
