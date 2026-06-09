from __future__ import annotations

import json
import re
from typing import Any

from ai_scrum_master.agents.crewai_contract import build_crewai_agent
from ai_scrum_master.core.agent_schemas import EvaluationOutput, dump_model
from ai_scrum_master.core.config import AgentProfileConfig, TaskProfileConfig
from ai_scrum_master.core.llm_json import normalize_llm_json_output
from ai_scrum_master.core.llm_setup import build_llm
from ai_scrum_master.core.logging import get_logger
from ai_scrum_master.core.prompts import render_prompt
from ai_scrum_master.core.quality import (
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

    def create_agent(self) -> Any:
        from ai_scrum_master.core.llm_setup import build_llm
        if not self.llm:
            # Evaluator cần sự ổn định và khắt khe nhất để chấm điểm (temperature = 0.0)
            self.llm = build_llm(temperature=0.0)
            
        role = self.profile.role if self.profile else "Story Quality Evaluator"
        goal = self.profile.goal if self.profile else "Validate story readiness and return APPROVED or REVISION with concrete issues."
        backstory = self.profile.backstory if self.profile else (
            "You enforce local rule checks, Scrum quality gates, domain isolation, and traceability "
            "before Jira or Slack action previews are prepared."
        )
        return build_crewai_agent(role=role, goal=goal, backstory=backstory, tools=[], verbose=True, llm=self.llm)

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
        warnings = list(dict.fromkeys(rule_result.get("warnings", []) + list(result.get("warnings", []))))
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


