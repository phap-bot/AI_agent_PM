from __future__ import annotations

import json
import re
from typing import Any

from ai_scrum_master.core.config import AgentProfileConfig
from ai_scrum_master.core.llm_setup import build_llm
from ai_scrum_master.core.logging import get_logger
from ai_scrum_master.core.prompts import render_prompt

FIBONACCI_POINTS = {1, 2, 3, 5, 8, 13}
READY = "READY"
NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
SPLIT_RECOMMENDED = "SPLIT_RECOMMENDED"

logger = get_logger(__name__)


class PlannerAgent:
    def __init__(
        self,
        llm: Any | None = None,
        use_llm: bool = True,
        profile: AgentProfileConfig | None = None,
    ) -> None:
        self.llm = llm
        self.use_llm = use_llm
        self.profile = profile

    def run(self, requirement: str, context: dict) -> dict:
        warnings = self._build_warnings(context)
        planning_status = self._classify_requirement(requirement)
        logger.info(
            "Planner started planning_status=%s context_documents=%s context_confidence=%s",
            planning_status,
            len(context.get("documents", [])),
            context.get("confidence"),
        )

        if not self.use_llm:
            logger.info("Planner using fallback because LLM is disabled")
            return self._fallback_story(requirement, warnings, planning_status)

        try:
            llm = self.llm or build_llm()
            logger.info("Planner LLM call started")
            raw_output = llm.call(self._build_prompt(requirement, context, planning_status))
            logger.info("Planner LLM call completed")
            story = self._parse_story(raw_output)
            logger.info("Planner parsed LLM JSON successfully")
            story["warnings"] = warnings + story.get("warnings", [])
            return self._normalize_story(story, requirement, warnings, planning_status)
        except Exception as exc:
            logger.exception("Planner failed to use LLM output; using fallback story")
            fallback = self._fallback_story(requirement, warnings, planning_status)
            fallback["warnings"].append(f"Planner LLM unavailable; used fallback story. Reason: {exc}")
            return fallback

    def _build_prompt(self, requirement: str, context: dict, planning_status: str) -> str:
        context_block = "\n\n".join(context.get("documents", [])) or "No project context was retrieved."
        role = self.profile.role if self.profile else "Planner Agent"
        goal = self.profile.goal if self.profile else "Convert the requirement into sprint-ready user stories."
        backstory = self.profile.backstory if self.profile else "You support an AI Scrum Master system."
        return render_prompt(
            "planner.md",
            role=role,
            goal=goal,
            backstory=backstory,
            requirement=requirement,
            planning_status=planning_status,
            context_block=context_block,
        )

    def _parse_story(self, raw_output: Any) -> dict:
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
            raise ValueError("Planner LLM did not return JSON.")
        return json.loads(text[start : end + 1])

    def _normalize_story(self, story: dict, requirement: str, warnings: list[str], planning_status: str) -> dict:
        fallback = self._fallback_story(requirement, warnings, planning_status)
        normalized = {
            "title": story.get("title") or fallback["title"],
            "user_story": story.get("user_story") or fallback["user_story"],
            "acceptance_criteria": story.get("acceptance_criteria") or fallback["acceptance_criteria"],
            "story_points": story.get("story_points") or fallback["story_points"],
            "tasks": story.get("tasks") or fallback["tasks"],
            "definition_of_done": story.get("definition_of_done") or fallback["definition_of_done"],
            "planning_status": story.get("planning_status") or fallback["planning_status"],
            "clarification_questions": story.get("clarification_questions") or fallback["clarification_questions"],
            "assumptions": story.get("assumptions") or fallback["assumptions"],
            "story_splits": story.get("story_splits") or fallback["story_splits"],
            "sprint_allocation": story.get("sprint_allocation") or fallback["sprint_allocation"],
            "warnings": story.get("warnings", []),
        }

        if normalized["planning_status"] not in {READY, NEEDS_CLARIFICATION, SPLIT_RECOMMENDED}:
            normalized["planning_status"] = planning_status
            normalized["warnings"].append("Planner returned invalid planning_status; reset by local classifier.")
        if planning_status != READY and normalized["planning_status"] != planning_status:
            normalized["planning_status"] = planning_status
            normalized["warnings"].append("Planner returned planning_status that conflicts with local classifier; reset by local classifier.")
        if normalized["story_points"] not in FIBONACCI_POINTS:
            normalized["story_points"] = fallback["story_points"]
            normalized["warnings"].append("Planner returned non-Fibonacci story points; reset to 3.")

        normalized["acceptance_criteria"] = self._complete_acceptance_criteria(
            normalized["acceptance_criteria"], fallback["acceptance_criteria"]
        )
        normalized["tasks"] = self._complete_tasks(normalized["tasks"], fallback["tasks"])
        normalized["definition_of_done"] = self._complete_definition_of_done(
            normalized["definition_of_done"], fallback["definition_of_done"]
        )

        if normalized["planning_status"] == READY:
            if normalized["clarification_questions"]:
                normalized["clarification_questions"] = []
                normalized["warnings"].append("Planner returned clarification questions for READY story; removed inconsistent questions.")
            normalized["story_splits"] = []
            normalized["sprint_allocation"] = []
        elif normalized["planning_status"] == NEEDS_CLARIFICATION:
            normalized["clarification_questions"] = normalized["clarification_questions"] or fallback["clarification_questions"]
            normalized["story_splits"] = []
            normalized["sprint_allocation"] = []
        elif normalized["planning_status"] == SPLIT_RECOMMENDED:
            normalized["clarification_questions"] = []
            normalized["story_splits"] = self._normalize_story_splits(
                normalized["story_splits"], fallback["story_splits"]
            )
            normalized["sprint_allocation"] = self._normalize_sprint_allocation(
                normalized["sprint_allocation"], fallback["sprint_allocation"]
            )
        logger.info(
            "Planner normalized story planning_status=%s story_points=%s warnings=%s",
            normalized["planning_status"],
            normalized["story_points"],
            len(normalized["warnings"]),
        )
        return normalized

    def _complete_acceptance_criteria(self, criteria: list[str], fallback: list[str]) -> list[str]:
        completed = [criterion for criterion in criteria if self._is_given_when_then(criterion)]
        for criterion in fallback:
            if len(completed) >= 3:
                break
            if criterion not in completed:
                completed.append(criterion)
        return completed

    def _is_given_when_then(self, criterion: str) -> bool:
        return all(re.search(rf"\b{token}\b", criterion, flags=re.IGNORECASE) for token in ("given", "when", "then"))

    def _complete_tasks(self, tasks: dict, fallback: dict[str, list[str]]) -> dict[str, list[str]]:
        completed = tasks if isinstance(tasks, dict) else {}
        return {
            key: self._task_items(completed.get(key)) or fallback[key]
            for key in ("be", "fe", "qa")
        }

    def _task_items(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]

    def _complete_definition_of_done(self, items: list[str], fallback: list[str]) -> list[str]:
        completed = [item.strip() for item in items if isinstance(item, str) and item.strip()]
        if len(completed) >= 4 and self._definition_of_done_covers_quality_bar(completed):
            return completed
        return list(dict.fromkeys(completed + fallback))

    def _definition_of_done_covers_quality_bar(self, items: list[str]) -> bool:
        text = " ".join(items).lower()
        required_terms = (
            ("acceptance", "criteria"),
            ("be", "backend", "fe", "frontend", "qa", "task", "implementation"),
            ("test", "qa", "validation"),
            ("review", "demo", "jira", "ready"),
        )
        return all(any(term in text for term in terms) for terms in required_terms)

    def _normalize_story_splits(self, story_splits: list[dict], fallback: list[dict]) -> list[dict]:
        source = story_splits or fallback
        normalized = []
        for index, split in enumerate(source):
            if not isinstance(split, dict):
                continue
            fallback_split = fallback[min(index, len(fallback) - 1)]
            normalized.append(
                {
                    "title": split.get("title") or fallback_split["title"],
                    "user_story": split.get("user_story") or fallback_split["user_story"],
                    "acceptance_criteria": self._complete_acceptance_criteria(
                        split.get("acceptance_criteria") or [], fallback_split["acceptance_criteria"]
                    ),
                    "story_points": split.get("story_points") if split.get("story_points") in FIBONACCI_POINTS else fallback_split["story_points"],
                    "tasks": self._complete_tasks(split.get("tasks") or {}, fallback_split["tasks"]),
                    "definition_of_done": self._complete_definition_of_done(
                        split.get("definition_of_done") or [], fallback_split["definition_of_done"]
                    ),
                }
            )
        return normalized or fallback

    def _normalize_sprint_allocation(self, sprint_allocation: list[dict], fallback: list[dict]) -> list[dict]:
        if not sprint_allocation:
            return fallback
        normalized = []
        for index, allocation in enumerate(sprint_allocation, start=1):
            if not isinstance(allocation, dict):
                continue
            stories = allocation.get("stories")
            if not stories:
                continue
            normalized.append({"sprint": allocation.get("sprint", index), "stories": stories})
        return normalized or fallback

    def _build_warnings(self, context: dict) -> list[str]:
        warnings = list(context.get("warnings", []))
        if not context.get("documents"):
            warnings.append("Story generated with limited project context.")
        if context.get("confidence", 1.0) < 0.5:
            warnings.append("Retrieved context confidence is low.")
        return warnings

    def _classify_requirement(self, requirement: str) -> str:
        lowered = requirement.lower().strip()
        words = lowered.split()
        ambiguous_terms = {"improve", "optimize", "enhance", "fix", "update", "better", "thing", "stuff"}
        oversized_terms = {"full", "complete", "entire", "portal", "platform", "dashboard", "billing", "analytics", "notifications", "admin"}

        if len(words) <= 3 or any(term == lowered or lowered.startswith(f"{term} ") for term in ambiguous_terms):
            return NEEDS_CLARIFICATION
        if sum(1 for term in oversized_terms if term in lowered) >= 3 or len(words) > 28:
            return SPLIT_RECOMMENDED
        return READY

    def _clarification_questions(self, requirement: str) -> list[str]:
        return [
            f"What user or role is the primary audience for '{requirement}'?",
            "What specific outcome or metric should this request improve?",
            "Are there existing flows, constraints, or systems the team must preserve?",
        ]

    def _split_stories(self, requirement: str) -> list[dict]:
        return [
            self._story_split("Foundation and access", requirement, 5),
            self._story_split("Core user workflow", requirement, 8),
            self._story_split("Admin and operations workflow", requirement, 8),
            self._story_split("Notifications and analytics", requirement, 5),
        ]

    def _clean_requirement_text(self, requirement: str) -> str:
        return requirement.strip().rstrip(".").lower()

    def _story_split(self, title: str, requirement: str, points: int) -> dict:
        return {
            "title": title,
            "user_story": f"As a stakeholder, I want the {title.lower()} slice delivered independently so that the team can progress on {self._clean_requirement_text(requirement)} incrementally.",
            "acceptance_criteria": [
                f"Given {title.lower()} is prioritized, when implementation starts, then scope is limited to that slice.",
                f"Given the slice is reviewed, when acceptance criteria are checked, then BE, FE, and QA impacts are clear.",
                f"Given the slice is complete, when QA validates it, then it can be accepted independently.",
            ],
            "story_points": points,
            "tasks": {
                "be": [
                    f"Define API, data, and integration changes needed for the {title.lower()} slice.",
                    f"Implement backend behavior for {title.lower()} with explicit error handling and logging impact reviewed.",
                ],
                "fe": [
                    f"Define user-facing flow and states for {title.lower()}, including loading, success, and failure states.",
                    f"Implement UI changes for {title.lower()} and confirm they match the accepted workflow.",
                ],
                "qa": [
                    f"Create Given/When/Then test scenarios for {title.lower()} covering happy path and edge cases.",
                    f"Run regression checks proving {title.lower()} can be accepted independently.",
                ],
            },
            "definition_of_done": self._default_definition_of_done(),
        }

    def _default_tasks(self, requirement: str) -> dict[str, list[str]]:
        cleaned_requirement = self._clean_requirement_text(requirement)
        return {
            "be": [
                f"Identify backend APIs, data contracts, auth/session impacts, and integration points required for {cleaned_requirement}.",
                f"Implement backend changes for {cleaned_requirement} with explicit handling for success, failure, and audit/logging needs.",
            ],
            "fe": [
                f"Map the user flow for {cleaned_requirement}, including entry point, loading state, success state, and error state.",
                f"Implement UI/client changes for {cleaned_requirement} and connect them to the backend contract.",
            ],
            "qa": [
                f"Create test scenarios for {cleaned_requirement} covering happy path, failure path, edge cases, and regression impact.",
                "Verify acceptance criteria, BE/FE integration, and any documented assumptions before Jira handoff.",
            ],
        }

    def _default_definition_of_done(self) -> list[str]:
        return [
            "All acceptance criteria pass with clear Given/When/Then validation evidence.",
            "BE and FE implementation tasks are complete, reviewed, and integrated without known blockers.",
            "QA scenarios cover happy path, failure path, edge cases, and relevant regression checks.",
            "Assumptions, warnings, and context gaps are documented or resolved before downstream action.",
            "Story is reviewed, demo-ready, and ready for Jira creation only after evaluator approval.",
        ]

    def _fallback_story(self, requirement: str, warnings: list[str], planning_status: str = READY) -> dict:
        story = {
            "title": "Draft Scrum Story",
            "user_story": f"As a stakeholder, I want {requirement.lower()} so that the team can deliver the requested outcome.",
            "acceptance_criteria": [
                "Given the requirement is approved, when planning starts, then the story is documented clearly.",
                "Given the team reviews the story, when acceptance criteria are checked, then at least 3 criteria are present.",
                "Given implementation begins, when tasks are assigned, then BE, FE, and QA work are separated.",
            ],
            "story_points": 3,
            "tasks": self._default_tasks(requirement),
            "definition_of_done": self._default_definition_of_done(),
            "planning_status": planning_status,
            "clarification_questions": [],
            "assumptions": list(warnings),
            "story_splits": [],
            "sprint_allocation": [],
            "warnings": list(warnings),
        }
        if planning_status == NEEDS_CLARIFICATION:
            story["clarification_questions"] = self._clarification_questions(requirement)
            story["warnings"].append("Requirement needs clarification before sprint-ready planning.")
        if planning_status == SPLIT_RECOMMENDED:
            story["story_splits"] = self._split_stories(requirement)
            story["sprint_allocation"] = [
                {"sprint": 1, "stories": [split["title"] for split in story["story_splits"][:2]]},
                {"sprint": 2, "stories": [split["title"] for split in story["story_splits"][2:]]},
            ]
            story["warnings"].append("Request appears too large for one sprint; split recommended.")
        logger.info("Planner fallback produced planning_status=%s", planning_status)
        return story
