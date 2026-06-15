from __future__ import annotations

import json
import re
import time
from typing import Any

from ai_scrum_master.core.agent_schemas import PlannerStoryOutput, build_planning_brief, dump_model
from ai_scrum_master.core.config import AgentProfileConfig, TaskProfileConfig, get_settings
from ai_scrum_master.core.domain_profiles import (
    PLANNER_CLARIFICATION_QUESTIONS,
    PLANNER_EVIDENCE_TEMPLATES,
    SPLIT_CAPABILITIES,
)
from ai_scrum_master.core.llm_setup import build_llm
from ai_scrum_master.core.llm_json import normalize_llm_json_output
from ai_scrum_master.core.logging import get_logger
from ai_scrum_master.core.prompts import render_prompt
from ai_scrum_master.core.quality import (
    FIBONACCI_POINTS,
    classify_requirement,
    filter_context_sources_for_requirement,
    filter_domain_contaminated_items,
    has_domain_contamination,
    is_generic_acceptance_criterion,
    is_given_when_then_ordered,
    is_placeholder_task,
    requirement_domain,
)
from ai_scrum_master.core.story_validator import item_similarity, is_task_actionable_for_group, similar_item_pairs

READY = "READY"
NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
SPLIT_RECOMMENDED = "SPLIT_RECOMMENDED"
NEEDS_SPLIT = "NEEDS_SPLIT"

logger = get_logger(__name__)

MAX_CONTEXT_BLOCK_CHARS = 6000
MAX_CONTEXT_ITEM_CHARS = 1200
MAX_CONTEXT_ITEMS = 3
MAX_REQUIREMENT_PROMPT_CHARS = 2500


class PlannerAgent:
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
        self.settings = get_settings()

    def run(self, requirement: str, context: dict, requirement_type: str | None = None, route: dict | None = None) -> dict:
        started_at = time.perf_counter()
        llm_latencies_ms: list[int] = []
        repair_attempts_used = 0
        route = route or context.get("route", {})
        filtered_context = self._filter_context_for_requirement(requirement, context)
        warnings = self._build_warnings(filtered_context)
        planning_status = self._classify_requirement(requirement, route)
        requirement_type = requirement_type or route.get("story_type") or classify_requirement(requirement)
        context_sources = filtered_context.get("retrieved_sources", [])
        logger.info(
            "Planner started planning_status=%s context_documents=%s context_confidence=%s",
            planning_status,
            len(filtered_context.get("documents", [])),
            filtered_context.get("confidence"),
        )

        if not self.use_llm:
            logger.info("Planner cannot generate story because LLM is disabled")
            unavailable = self._llm_unavailable_story(requirement, warnings, planning_status, context_sources, requirement_type, route)
            return self._attach_latency_metadata(unavailable, started_at, llm_latencies_ms, repair_attempts_used)

        try:
            llm = self.llm or build_llm()
            messages = self._build_messages(requirement, filtered_context, planning_status)
            logger.info(
                "LLM trace planner request stage=initial messages=%s prompt_chars=%s context_sources=%s retrieval_status=%s",
                len(messages),
                sum(len(message["content"]) for message in messages),
                len(context_sources),
                filtered_context.get("retrieval_status"),
            )
            llm_started_at = time.perf_counter()
            raw_output = llm.call(messages)
            initial_llm_ms = self._elapsed_ms(llm_started_at)
            llm_latencies_ms.append(initial_llm_ms)
            logger.info("LLM trace planner response stage=initial raw_chars=%s latency_ms=%s", len(str(raw_output)), initial_llm_ms)
            logger.info("--- LLM THINKING OUTPUT (INITIAL) ---\n%s\n---------------------------------------", str(raw_output))
            story = self._parse_story(raw_output)
            logger.info("LLM trace planner parsed stage=initial keys=%s", sorted(story.keys()))
            story["warnings"] = warnings + story.get("warnings", [])
            normalized = self._normalize_story(story, requirement, warnings, planning_status, context_sources, requirement_type, route)
            return self._attach_latency_metadata(normalized, started_at, llm_latencies_ms, repair_attempts_used)
        except Exception as exc:
            logger.exception("Planner failed to use LLM output")
            unavailable = self._llm_unavailable_story(requirement, warnings, planning_status, context_sources, requirement_type, route)
            failure_type = "planner_timeout" if "timeout" in str(exc).lower() or "timed out" in str(exc).lower() else "planner_exception"
            unavailable["failure_type"] = failure_type
            unavailable["timed_out"] = failure_type == "planner_timeout"
            unavailable["warnings"].append(f"{failure_type}: Planner LLM unavailable or returned invalid output. Reason: {exc}")
            return self._attach_latency_metadata(unavailable, started_at, llm_latencies_ms, repair_attempts_used)

    def _build_messages(self, requirement: str, context: dict, planning_status: str) -> list[dict[str, str]]:
        return [
            {"role": "user", "content": self._build_prompt(requirement, context, planning_status)},
        ]



    def _build_prompt(self, requirement: str, context: dict, planning_status: str) -> str:
        context_block = self._build_context_block(context)
        role = self.profile.role if self.profile else "Planner Agent"
        goal = self.profile.goal if self.profile else "Convert the requirement into sprint-ready user stories."
        backstory = self.profile.backstory if self.profile else "You support an AI Scrum Master system."
        task_description = (
            self.task_profile.description
            if self.task_profile
            else "Produce one sprint-ready user story or a clarification/split decision from requirement and selected documentation context."
        )
        expected_output = (
            self.task_profile.expected_output
            if self.task_profile
            else "JSON story with title, user_story, acceptance_criteria, story_points, tasks, definition_of_done, assumptions, context_sources, and planning_status."
        )
        try:
            from ai_scrum_master.core.prompts import render_prompt as load_prompt
            few_shot = load_prompt("planner_few_shot.md")
        except Exception:
            few_shot = ""

        return render_prompt(
            self._prompt_name("planner"),
            role=role,
            goal=goal,
            backstory=backstory,
            task_description=task_description,
            expected_output=expected_output,
            requirement=self._compact_requirement_for_prompt(requirement),
            context_block=context_block,
            planning_status=planning_status,
            few_shot_examples=few_shot,
        )

    def _attach_latency_metadata(
        self,
        story: dict,
        started_at: float,
        llm_latencies_ms: list[int],
        repair_attempts_used: int,
    ) -> dict:
        latency_ms = self._elapsed_ms(started_at)
        stage_latencies = dict(story.get("stage_latencies_ms", {}))
        stage_latencies["planner_ms"] = latency_ms
        if llm_latencies_ms:
            stage_latencies["planner_llm_ms"] = sum(llm_latencies_ms)
            stage_latencies["planner_initial_llm_ms"] = llm_latencies_ms[0]
        if len(llm_latencies_ms) > 1:
            stage_latencies["planner_repair_llm_ms"] = sum(llm_latencies_ms[1:])
        story["latency_ms"] = latency_ms
        story["stage_latencies_ms"] = stage_latencies
        story["repair_attempts_used"] = repair_attempts_used
        logger.info(
            "Planner completed planning_status=%s latency_ms=%s repair_attempts_used=%s",
            story.get("planning_status"),
            latency_ms,
            repair_attempts_used,
        )
        return self._validate_story_output(story)

    def _elapsed_ms(self, started_at: float) -> int:
        return max(0, round((time.perf_counter() - started_at) * 1000))

    def _prompt_name(self, prompt_base: str) -> str:
        version = (self.settings.planner_prompt_version or "").strip().lower()
        if version in {"v1", "v2"}:
            return f"{prompt_base}.md"
        if version and version not in {"default", "current"}:
            return f"{prompt_base}_{version}.md"
        return f"{prompt_base}.md"

    def _filter_context_for_requirement(self, requirement: str, context: dict) -> dict:
        if "selected_context_sources" in context or "ignored_context_sources" in context:
            filtered = dict(context)
            selected_sources = filtered.get("selected_context_sources") or filtered.get("retrieved_sources", [])
            filtered["planning_brief"] = build_planning_brief(
                requirement=requirement,
                sources=selected_sources,
                retrieval_status=filtered.get("retrieval_status", "empty"),
                confidence=filtered.get("confidence", 0.0),
                planning_instruction=(
                    "Use only usable_evidence excerpts as project documentation evidence. "
                    "Ignored context must not influence the story."
                ),
            )
            return filtered
        filtered = dict(context)
        selected_sources, ignored_sources = filter_context_sources_for_requirement(requirement, context.get("retrieved_sources", []))
        if selected_sources or ignored_sources:
            selected_ids = {source.get("id") for source in selected_sources if source.get("id")}
            selected_excerpts = {source.get("excerpt") for source in selected_sources if source.get("excerpt")}
            filtered["selected_context_sources"] = selected_sources
            filtered["ignored_context_sources"] = ignored_sources
            filtered["retrieved_sources"] = selected_sources
            filtered["context_snippets"] = [
                snippet
                for snippet in context.get("context_snippets", [])
                if any(
                    str(source.get("source", "")) in snippet and str(source.get("excerpt", ""))[:40] in snippet
                    for source in selected_sources
                )
            ]
            matches = [
                match
                for match in context.get("matches", [])
                if match.get("id") in selected_ids or match.get("document") in selected_excerpts
            ]
            filtered["matches"] = matches
            selected_documents = [match.get("document", "") for match in matches if match.get("document")]
            if not selected_documents and selected_sources:
                selected_documents = [
                    source.get("excerpt", "")
                    for source in selected_sources
                    if isinstance(source.get("excerpt"), str) and source.get("excerpt", "").strip()
                ]
            filtered["documents"] = selected_documents
            filtered["planning_brief"] = build_planning_brief(
                requirement=requirement,
                sources=selected_sources,
                retrieval_status=filtered.get("retrieval_status", "empty"),
                confidence=filtered.get("confidence", 0.0),
                planning_instruction=(
                    "Use only usable_evidence excerpts as project documentation evidence. "
                    "Ignored context must not influence the story."
                ),
            )
            if ignored_sources:
                warnings = list(filtered.get("warnings", []))
                warnings.append("Ignored retrieved context that was unrelated to the current requirement domain.")
                filtered["warnings"] = warnings
        return filtered

    def _compact_requirement_for_prompt(self, requirement: str) -> str:
        return self._truncate_context_text(requirement, MAX_REQUIREMENT_PROMPT_CHARS)

    def _build_context_block(self, context: dict) -> str:
        snippets = [snippet for snippet in context.get("context_snippets", []) if isinstance(snippet, str) and snippet.strip()]
        if snippets:
            return self._compact_context_items(snippets)

        matches = context.get("matches", [])
        if isinstance(matches, list) and matches:
            blocks = []
            for index, match in enumerate(matches[:MAX_CONTEXT_ITEMS], start=1):
                if not isinstance(match, dict):
                    continue
                metadata = match.get("metadata") if isinstance(match.get("metadata"), dict) else {}
                source = metadata.get("source") or metadata.get("file_name") or match.get("id") or "unknown source"
                chunk_index = metadata.get("chunk_index", "?")
                document = self._truncate_context_text(str(match.get("document", "")).strip())
                blocks.append(
                    f"[{index}] source={source} chunk={chunk_index} score={match.get('score', 0.0)}: {document}"
                )
            if blocks:
                return self._compact_context_items(blocks)

        documents = [document for document in context.get("documents", []) if isinstance(document, str) and document.strip()]
        return self._compact_context_items(documents) if documents else "No project context was retrieved."

    def _compact_context_items(self, items: list[str]) -> str:
        compacted = []
        total_chars = 0
        for item in items[:MAX_CONTEXT_ITEMS]:
            truncated = self._truncate_context_text(item)
            if total_chars + len(truncated) > MAX_CONTEXT_BLOCK_CHARS:
                remaining = MAX_CONTEXT_BLOCK_CHARS - total_chars
                if remaining <= 0:
                    break
                truncated = self._truncate_context_text(truncated, remaining)
            compacted.append(truncated)
            total_chars += len(truncated)
        return "\n\n".join(compacted) or "No project context was retrieved."

    def _truncate_context_text(self, value: str, limit: int = MAX_CONTEXT_ITEM_CHARS) -> str:
        normalized = " ".join(value.split())
        if len(normalized) <= limit:
            return normalized
        return f"{normalized[: max(0, limit - 15)].rstrip()} ...[truncated]"

    def _parse_story(self, raw_output: Any) -> dict:
        if isinstance(raw_output, dict):
            return self._unwrap_story_payload(raw_output)

        text = normalize_llm_json_output(raw_output)
        
        # Remove <think>...</think> blocks if present
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        
        return self._unwrap_story_payload(json.loads(text))

    def _unwrap_story_payload(self, payload: dict) -> dict:
        story = payload.get("story")
        if isinstance(story, dict):
            merged = dict(story)
            for key in ("retrieval_status", "retrieval_threshold", "confidence", "raw_match_count", "context_sources", "warnings"):
                if key in payload and key not in merged:
                    merged[key] = payload[key]
            return merged
        return payload

    def _normalize_story(
        self,
        story: dict,
        requirement: str,
        warnings: list[str],
        planning_status: str,
        context_sources: list[dict] | None = None,
        requirement_type: str | None = None,
        route: dict | None = None,
    ) -> dict:
        requirement_type = requirement_type or classify_requirement(requirement)
        warnings_out = [w for w in story.get("warnings", []) if isinstance(w, str) and not w.startswith("Planner ")]
        normalized = {
            "requirement": requirement,
            "title": self._clean_text_field(requirement, story.get("title") or requirement.strip(), requirement.strip(), "title", warnings_out),
            "story_type": requirement_type,
            "jira_issue_type": story.get("jira_issue_type") or ("Epic" if requirement_type == "oversized_request" else "Task" if requirement_type == "process_improvement" else "Story"),
            "user_story": self._normalize_user_story(
                self._clean_text_field(requirement, story.get("user_story") or "", "", "user_story", warnings_out),
            ),
            "acceptance_criteria": self._clean_list(requirement, story.get("acceptance_criteria"), "acceptance_criteria", warnings_out),
            "story_points": story.get("story_points"),
            "tasks": self._clean_tasks(requirement, story.get("tasks"), warnings_out),
            "definition_of_done": self._clean_list(requirement, story.get("definition_of_done"), "definition_of_done", warnings_out),
            "planning_status": story.get("planning_status") or planning_status,
            "clarification_questions": self._clean_list(requirement, story.get("clarification_questions"), "clarification_questions", warnings_out),
            "assumptions": self._clean_list(requirement, story.get("assumptions"), "assumptions", warnings_out),
            "story_splits": self._clean_story_splits(requirement, story.get("story_splits"), warnings_out),
            "sprint_allocation": self._clean_sprint_allocation(story.get("sprint_allocation"), warnings_out),
            "context_sources": self._normalize_context_sources(story.get("context_sources"), context_sources or [], requirement),
            "route": route or {},
            "warnings": warnings_out,
        }

        if normalized["planning_status"] not in {READY, NEEDS_CLARIFICATION, NEEDS_SPLIT, SPLIT_RECOMMENDED, "REVISION"}:
            normalized["planning_status"] = planning_status
            normalized["warnings"].append("Planner returned invalid planning_status; reset by local classifier.")
        if normalized["planning_status"] == READY and normalized["story_points"] not in FIBONACCI_POINTS:
            normalized["story_points"] = None
            normalized["warnings"].append("Planner returned missing or non-Fibonacci story points; evaluator must request revision.")

        self._add_missing_output_warnings(normalized)

        if normalized["planning_status"] == READY:
            self._complete_ready_fields_from_evidence(normalized, requirement, context_sources or [], route or {})
            if normalized["clarification_questions"]:
                normalized["clarification_questions"] = []
                normalized["warnings"].append("Planner returned clarification questions for READY story; removed inconsistent questions.")
            normalized["story_splits"] = []
            normalized["sprint_allocation"] = []
        elif normalized["planning_status"] == NEEDS_CLARIFICATION:
            self._clear_ready_fields_for_clarification(normalized, requirement)
            normalized["story_splits"] = []
            normalized["sprint_allocation"] = []
        elif normalized["planning_status"] in {NEEDS_SPLIT, SPLIT_RECOMMENDED}:
            normalized["clarification_questions"] = []
            self._complete_split_fields(normalized, requirement)
        logger.info(
            "Planner normalized story planning_status=%s story_points=%s warnings=%s",
            normalized["planning_status"],
            normalized["story_points"],
            len(normalized["warnings"]),
        )
        return self._validate_story_output(normalized)

    def _clean_text_field(self, requirement: str, value: Any, fallback: str, field_name: str, warnings: list[str]) -> str:
        if isinstance(value, str) and self._is_sample_placeholder(value):
            warnings.append(f"Planner returned sample placeholder text for {field_name}; replaced from requirement.")
            return fallback
        if has_domain_contamination(requirement, value):
            warnings.append(f"Planner removed unrelated-domain content from {field_name} using local requirement rules.")
            return fallback
        if not isinstance(value, str):
            warnings.append(f"Planner returned invalid {field_name}; expected a string.")
            return fallback
        return value.strip()

    def _clean_list(self, requirement: str, values: Any, field_name: str, warnings: list[str]) -> list[Any]:
        if not isinstance(values, list):
            if values not in (None, ""):
                warnings.append(f"Planner returned invalid {field_name}; expected a list.")
            return []
            
        normalized_values = []
        for item in values:
            if isinstance(item, dict):
                given = str(item.get("given") or item.get("Given") or "").strip()
                when = str(item.get("when") or item.get("When") or "").strip()
                then = str(item.get("then") or item.get("Then") or "").strip()
                if given or when or then:
                    parts = []
                    if given: parts.append(f"Given {given}")
                    if when: parts.append(f"When {when}")
                    if then: parts.append(f"Then {then}")
                    normalized_values.append(", ".join(parts))
                else:
                    normalized_values.append(" ".join(str(v) for v in item.values() if v))
            else:
                normalized_values.append(item)
                
        kept, removed = filter_domain_contaminated_items(requirement, normalized_values)
        sample_removed = [item for item in kept if isinstance(item, str) and self._is_sample_placeholder(item)]
        kept = [item for item in kept if not (isinstance(item, str) and self._is_sample_placeholder(item))]
        if removed:
            warnings.append(f"Planner removed unrelated-domain content from {field_name} using local requirement rules.")
        if sample_removed:
            warnings.append(f"Planner removed sample placeholder content from {field_name}.")
        return [item for item in kept if isinstance(item, str) and item.strip()]

    def _clean_tasks(self, requirement: str, tasks: Any, warnings: list[str]) -> dict[str, list[str]]:
        source = tasks if isinstance(tasks, dict) else {}
        cleaned: dict[str, list[str]] = {}
        removed_any = False
        for key in ("be", "fe", "qa"):
            values = source.get(key, []) if isinstance(source.get(key, []), list) else []
            kept, removed = filter_domain_contaminated_items(requirement, values)
            sample_removed = [item for item in kept if isinstance(item, str) and self._is_sample_placeholder(item)]
            kept = [item for item in kept if not (isinstance(item, str) and self._is_sample_placeholder(item))]
            removed_any = removed_any or bool(removed)
            removed_any = removed_any or bool(sample_removed)
            cleaned[key] = [item for item in kept if isinstance(item, str) and item.strip()]
        if removed_any:
            warnings.append("Planner removed unrelated-domain content from tasks using local requirement rules.")
        return cleaned

    def _normalize_user_story(self, user_story: str) -> str:
        return user_story.strip() if isinstance(user_story, str) else ""

    def _complete_ready_fields_from_evidence(self, story: dict, requirement: str, context_sources: list[dict], route: dict | None = None) -> None:
        if not context_sources:
            return
        evidence_text = " ".join(str(source.get("excerpt", "")) for source in context_sources).lower()
        added = False

        if self._is_sample_placeholder(story.get("title", "")):
            story["title"] = requirement.strip().rstrip(".")
            added = True
        if not self._is_user_story_ready(story.get("user_story", "")):
            story["user_story"] = self._evidence_user_story(requirement, evidence_text)
            added = True

        raw_criteria = story.get("acceptance_criteria", [])
        criteria = []
        for criterion in raw_criteria:
            if not isinstance(criterion, str) or is_generic_acceptance_criterion(criterion):
                continue
            if not is_given_when_then_ordered(criterion):
                continue
            if any(item_similarity(criterion, existing) >= 0.62 for existing in criteria):
                continue
            criteria.append(criterion)
        if len(criteria) != len(raw_criteria):
            story["warnings"].append("Planner removed weak acceptance criteria before evidence completion.")
            added = True
        for candidate in self._evidence_acceptance_criteria(requirement, evidence_text, route or {}):
            if len(criteria) >= 3:
                break
            if candidate not in criteria and not any(item_similarity(candidate, criterion) >= 0.62 for criterion in criteria):
                criteria.append(candidate)
                added = True
        story["acceptance_criteria"] = criteria

        tasks = story.get("tasks", {}) if isinstance(story.get("tasks"), dict) else {"be": [], "fe": [], "qa": []}
        for group in ("be", "fe", "qa"):
            values = tasks.get(group, [])
            if isinstance(values, list):
                cleaned_values = [
                    item
                    for item in values
                    if isinstance(item, str)
                    and item.strip()
                    and not is_placeholder_task(item)
                    and is_task_actionable_for_group(item, group)
                ]
                if len(cleaned_values) != len(values):
                    story["warnings"].append(f"Planner removed generic {group.upper()} tasks before evidence completion.")
                    added = True
                tasks[group] = cleaned_values
        for group, candidates in self._evidence_tasks(requirement, evidence_text, route or {}).items():
            tasks.setdefault(group, [])
            if not tasks[group] and candidates:
                tasks[group].append(candidates[0])
                added = True
        story["tasks"] = tasks

        dod = list(story.get("definition_of_done", []))
        for candidate in self._evidence_definition_of_done(requirement, evidence_text, route or {}):
            if len(dod) >= 4:
                break
            if candidate not in dod:
                dod.append(candidate)
                added = True
        story["definition_of_done"] = dod

        if story.get("story_points") not in FIBONACCI_POINTS:
            points = self._estimate_story_points_with_llm(requirement, evidence_text)
            if points:
                story["story_points"] = points
            added = True

        if added:
            story["warnings"].append("Planner completed missing READY fields from retrieved evidence after repair.")

    def _evidence_acceptance_criteria(self, requirement: str, evidence_text: str, route: dict | None = None) -> list[str]:
        domain = self._evidence_domain(requirement, evidence_text, route or {})
        return list(self._evidence_template(domain).get("acceptance_criteria", []))

    def _evidence_user_story(self, requirement: str, evidence_text: str) -> str:
        domain = self._evidence_domain(requirement, evidence_text, {})
        return str(
            self._evidence_template(domain).get(
                "user_story",
                f"As a user, I want {requirement.strip().rstrip('.')}, so that the documented outcome can be achieved.",
            )
        )

    def _evidence_tasks(self, requirement: str, evidence_text: str, route: dict | None = None) -> dict[str, list[str]]:
        domain = self._evidence_domain(requirement, evidence_text, route or {})
        tasks = self._evidence_template(domain).get("tasks", {})
        return {group: list(values) for group, values in tasks.items()} if isinstance(tasks, dict) else {"be": [], "fe": [], "qa": []}

    def _estimate_story_points_with_llm(self, requirement: str, evidence_text: str) -> int | None:
        try:
            from ai_scrum_master.core.llm_setup import build_llm
            import json
            llm = getattr(self, "llm", None) or build_llm()
            messages = [
                {"role": "system", "content": "You are an expert Agile Planner. Estimate story points (1, 2, 3, 5, 8, 13) based on the requirement and context. Output ONLY a valid JSON object with a single key 'story_points' containing the integer."},
                {"role": "user", "content": f"Requirement: {requirement}\nContext: {evidence_text}"}
            ]
            raw_output = llm.call(messages)
            from ai_scrum_master.core.llm_json import normalize_llm_json_output
            json_text = normalize_llm_json_output(raw_output)
            data = json.loads(json_text)
            points = data.get("story_points")
            if points in FIBONACCI_POINTS:
                return points
        except Exception as e:
            logger.warning(f"Failed to estimate story points dynamically: {e}")
        return None

    def _evidence_definition_of_done(self, requirement: str, evidence_text: str, route: dict | None = None) -> list[str]:
        domain = self._evidence_domain(requirement, evidence_text, route or {})
        return list(self._evidence_template(domain).get("definition_of_done", []))

    def _evidence_template(self, domain: str) -> dict:
        return PLANNER_EVIDENCE_TEMPLATES.get(domain, PLANNER_EVIDENCE_TEMPLATES["general"])

    def _evidence_domain(self, requirement: str, evidence_text: str, route: dict | None = None) -> str:
        route_domain = (route or {}).get("domain")
        if route_domain in {"auth_google_login", "auth_general_login"}:
            return "auth"
        if route_domain in {"checkout_payment_retry", "checkout_duplicate_payment"}:
            return "checkout"
        if route_domain == "sprint_planning_process":
            return "sprint"
        combined = f"{requirement} {evidence_text}".lower()
        if any(term in combined for term in ("oauth", "jwt", "google", "login", "authentication", "token")):
            return "auth"
        if any(term in combined for term in ("checkout", "payment", "order", "coupon", "inventory", "shipping", "cart")):
            return "checkout"
        if any(term in combined for term in ("notification", "slack", "email", "webhook", "alert")):
            return "notification"
        if any(term in combined for term in ("sprint planning", "sprint goal", "product backlog", "sprint backlog")):
            return "sprint"
        return "general"

    def _is_sample_placeholder(self, value: str) -> bool:
        lowered = value.lower()
        return any(
            phrase in lowered
            for phrase in (
                "context-specific",
                "documented action",
                "documented precondition",
                "documented success outcome",
                "sample title",
            )
        )

    def _is_user_story_ready(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return ("As a" in value or "As an" in value) and "I want" in value and "so that" in value.lower()

    def _normalize_context_sources(self, sources: Any, fallback: list[dict], requirement: str) -> list[dict]:
        if not isinstance(sources, list):
            return fallback
        normalized = []
        for source in sources:
            if not isinstance(source, dict):
                continue
            normalized_source = dict(source)
            if not normalized_source.get("source"):
                normalized_source["source"] = "unknown"
            else:
                normalized_source["source"] = str(normalized_source["source"])
            if "chunk_index" not in normalized_source and "chunk" in normalized_source:
                normalized_source["chunk_index"] = normalized_source["chunk"]
            normalized.append(normalized_source)
        selected, _ignored = filter_context_sources_for_requirement(requirement, normalized)
        return selected or fallback

    def _clean_story_splits(self, requirement: str, story_splits: Any, warnings: list[str]) -> list[dict]:
        if not isinstance(story_splits, list):
            return []
        normalized = []
        for split in story_splits:
            if not isinstance(split, dict):
                continue
            normalized.append(
                {
                    "title": self._clean_text_field(requirement, split.get("title") or "", "", "story_splits.title", warnings),
                    "user_story": self._normalize_user_story(
                        self._clean_text_field(requirement, split.get("user_story") or "", "", "story_splits.user_story", warnings)
                    ),
                    "acceptance_criteria": self._clean_list(requirement, split.get("acceptance_criteria"), "story_splits.acceptance_criteria", warnings),
                    "story_points": split.get("story_points") if split.get("story_points") in FIBONACCI_POINTS else None,
                    "tasks": self._clean_tasks(requirement, split.get("tasks"), warnings),
                    "definition_of_done": self._clean_list(requirement, split.get("definition_of_done"), "story_splits.definition_of_done", warnings),
                }
            )
        return normalized

    def _clean_sprint_allocation(self, sprint_allocation: Any, warnings: list[str]) -> list[dict]:
        if not isinstance(sprint_allocation, list):
            if sprint_allocation not in (None, ""):
                warnings.append("Planner returned invalid sprint_allocation; expected a list.")
            return []
        cleaned = [item for item in sprint_allocation if isinstance(item, dict)]
        if len(cleaned) != len(sprint_allocation):
            warnings.append("Planner removed invalid sprint_allocation items; expected objects.")
        return cleaned

    def _complete_split_fields(self, story: dict, requirement: str) -> None:
        capabilities = self._named_capabilities(requirement)
        if not story.get("story_splits") and capabilities:
            story["story_splits"] = [
                {
                    "title": f"{capability.title()} capability",
                    "user_story": f"As a user, I want {capability} capability, so that the portal can deliver that business outcome independently.",
                    "acceptance_criteria": [],
                    "story_points": None,
                    "tasks": {"be": [], "fe": [], "qa": []},
                    "definition_of_done": [],
                }
                for capability in capabilities
            ]
            story["warnings"].append("Planner completed story_splits from named capabilities for oversized request.")
        if not story.get("sprint_allocation") and story.get("story_splits"):
            story["sprint_allocation"] = [
                {
                    "sprint": index,
                    "stories": [split.get("title", "")],
                    "reason": "Split from oversized parent request; refine before Jira creation.",
                }
                for index, split in enumerate(story["story_splits"], start=1)
            ]
            story["warnings"].append("Planner completed sprint_allocation for oversized split review.")

    def _named_capabilities(self, requirement: str) -> list[str]:
        text = requirement.lower()
        return [item for item in SPLIT_CAPABILITIES if item in text]

    def _add_missing_output_warnings(self, story: dict) -> None:
        if story["planning_status"] == READY:
            required = {
                "user_story": story.get("user_story"),
                "acceptance_criteria": story.get("acceptance_criteria"),
                "story_points": story.get("story_points"),
                "definition_of_done": story.get("definition_of_done"),
            }
            for field_name, value in required.items():
                if value in (None, "", []):
                    story["warnings"].append(f"Planner LLM did not provide {field_name}; evaluator must request revision.")
            for group in ("be", "fe", "qa"):
                if not story.get("tasks", {}).get(group):
                    story["warnings"].append(f"Planner LLM did not provide {group.upper()} tasks; evaluator must request revision.")

    def _clear_ready_fields_for_clarification(self, story: dict, requirement: str) -> None:
        had_ready_fields = (
            bool(story.get("user_story"))
            or bool(story.get("acceptance_criteria"))
            or story.get("story_points") is not None
            or any(story.get("tasks", {}).get(group) for group in ("be", "fe", "qa"))
            or bool(story.get("definition_of_done"))
        )
        story["user_story"] = ""
        story["acceptance_criteria"] = []
        story["story_points"] = None
        story["tasks"] = {"be": [], "fe": [], "qa": []}
        story["definition_of_done"] = []
        if had_ready_fields:
            story["warnings"].append("Planner removed ready-story fields because planning_status is NEEDS_CLARIFICATION.")
        if len(story.get("clarification_questions", [])) < 3:
            existing_questions = [
                question
                for question in story.get("clarification_questions", [])
                if isinstance(question, str) and question.strip()
            ]
            for question in self._clarification_questions_for_requirement(requirement):
                if len(existing_questions) >= 3:
                    break
                if question not in existing_questions:
                    existing_questions.append(question)
            story["clarification_questions"] = existing_questions
            story["warnings"].append("Planner completed missing clarification questions for NEEDS_CLARIFICATION.")

    def _clarification_questions_for_requirement(self, requirement: str) -> list[str]:
        domain = requirement_domain(requirement)
        return list(PLANNER_CLARIFICATION_QUESTIONS.get(domain, PLANNER_CLARIFICATION_QUESTIONS["general"]))



    def _build_warnings(self, context: dict) -> list[str]:
        warnings = list(context.get("warnings", []))
        if not context.get("documents") and not context.get("retrieved_sources") and not context.get("context_snippets"):
            warnings.append("Story generated with limited project context.")
        if context.get("confidence", 1.0) < 0.5:
            warnings.append("Retrieved context confidence is low.")
        return warnings

    def _classify_requirement(self, requirement: str, route: dict | None = None) -> str:
        route = route or {}
        if route.get("domain") == "benchmark_case":
            return READY

        requirement_type = classify_requirement(requirement)
        if requirement_type == "ambiguous_request":
            return NEEDS_CLARIFICATION
        if requirement_type == "oversized_request":
            return SPLIT_RECOMMENDED

        return READY

    def _llm_unavailable_story(
        self,
        requirement: str,
        warnings: list[str],
        planning_status: str = READY,
        context_sources: list[dict] | None = None,
        requirement_type: str | None = None,
        route: dict | None = None,
    ) -> dict:
        selected_context_sources, _ignored = filter_context_sources_for_requirement(requirement, context_sources or [])
        clarification_questions = (
            self._clarification_questions_for_requirement(requirement)
            if planning_status == NEEDS_CLARIFICATION
            else []
        )
        return self._validate_story_output({
            "title": requirement.strip(),
            "user_story": "",
            "acceptance_criteria": [],
            "story_points": None,
            "story_type": requirement_type or classify_requirement(requirement),
            "tasks": {"be": [], "fe": [], "qa": []},
            "definition_of_done": [],
            "planning_status": "REVISION" if planning_status == READY else planning_status,
            "clarification_questions": clarification_questions,
            "assumptions": list(warnings),
            "story_splits": [],
            "sprint_allocation": [],
            "context_sources": selected_context_sources,
            "route": route or {},
            "fallback_used": False,
            "warnings": list(warnings) + ["Planner requires an LLM-generated, context-grounded story; no fixed template fallback was used."],
        })

    def _validate_story_output(self, payload: dict) -> dict:
        return dump_model(PlannerStoryOutput.model_validate(payload))
