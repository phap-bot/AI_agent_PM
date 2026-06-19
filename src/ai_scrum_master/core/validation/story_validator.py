from __future__ import annotations

import copy
import re
from typing import Any

from ai_scrum_master.core.config.domain_profiles import CONCEPT_TERMS, SPLIT_CAPABILITIES, STRONG_DOMAIN_TERMS
from ai_scrum_master.core.validation.quality import (
    AMBIGUOUS_REQUEST,
    FIBONACCI_POINTS,
    OVERSIZED_REQUEST,
    domain_contamination_issues,
    is_given_when_then_ordered,
    is_placeholder_task,
    is_user_story_task,
    validate_story_against_requirement,
)
from ai_scrum_master.core.validation.quality_gate import expected_relevance_for_requirement, normalize_source_name

READY = "READY"
REVISION = "REVISION"
NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
SPLIT_RECOMMENDED = "SPLIT_RECOMMENDED"
NEEDS_SPLIT = "NEEDS_SPLIT"

SIMILARITY_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "because",
    "by",
    "for",
    "given",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "so",
    "that",
    "the",
    "then",
    "to",
    "when",
    "with",
    "without",
}

TASK_REQUIRED_TERMS = {
    "be": ("backend", "api", "server", "database", "order", "payment", "callback", "token", "jwt", "inventory", "oauth", "define", "facilitation", "planning", "process", "endpoint", "crud", "service", "logic", "validation", "webhook", "controller", "model", "handler", "integration", "middleware", "session", "auth"),
    "fe": ("frontend", "ui", "page", "button", "message", "display", "route", "client", "form", "prompt", "checklist", "workspace", "template", "capture", "view", "modal", "component", "screen", "layout", "select", "input", "interface"),
    "qa": ("qa", "test", "testing", "validate", "validation", "verify", "scenario", "regression", "automation", "mock", "assert", "coverage", "evidence", "confirm", "check", "ensure", "review"),
}

TASK_FORBIDDEN_TERMS = {
    "be": ("ui", "button", "page"),
    "fe": ("server", "database"),
    "qa": (),
}


def validate_post_generation(requirement: str, story: dict[str, Any] | None, context: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    if story is None:
        return {
            "passed": False,
            "issues": ["Planner did not return a story."],
            "warnings": [],
            "normalized_story": None,
            "normalized_planning_status": REVISION,
        }

    issues: list[str] = []
    warnings: list[str] = []
    planning_status = story.get("planning_status", READY)
    domain = route.get("domain", "unknown")

    if domain == "ambiguous_request":
        issues.extend(_ambiguous_issues(story))
        return _result(story, issues, warnings, NEEDS_CLARIFICATION)

    if domain == "oversized_request":
        issues.extend(_oversized_issues(story, requirement))
        return _result(story, issues, warnings, SPLIT_RECOMMENDED)

    domain_for_validation = route.get("domain", "general") if route else "general"
    issues.extend(domain_contamination_issues(domain_for_validation, requirement, story))
    issues.extend(_required_context_issues(context))
    issues.extend(_forbidden_domain_issues(story, route))
    warnings.extend(_optional_context_warnings(context))

    if planning_status == READY:
        issues.extend(_ready_story_shape_issues(story))
        issues.extend(_required_concept_issues(story, route))
    elif planning_status not in {REVISION, NEEDS_SPLIT, SPLIT_RECOMMENDED, NEEDS_CLARIFICATION}:
        issues.append("planning_status must use a valid enum value.")

    return _result(story, issues, warnings, REVISION if issues else planning_status)


def evaluate_planner_output(requirement_type: str, requirement: str, story: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    issues = validate_story_against_requirement(requirement_type, requirement, story)
    criteria = story.get("acceptance_criteria", [])
    tasks = story.get("tasks", {}) if isinstance(story.get("tasks"), dict) else {}
    dod = story.get("definition_of_done", [])
    expected_sources = set(expected_relevance_for_requirement(requirement))
    actual_sources = {
        normalize_source_name(str(source.get("source", "")))
        for source in story.get("context_sources", [])
        if isinstance(source, dict)
    } or {
        normalize_source_name(str(source.get("source", "")))
        for source in context.get("retrieved_sources", [])
        if isinstance(source, dict)
    }

    metrics = {
        "planning_status": story.get("planning_status"),
        "story_type": story.get("story_type"),
        "acceptance_criteria_count": len(criteria) if isinstance(criteria, list) else 0,
        "given_when_then_ordered_count": sum(1 for item in criteria if is_given_when_then_ordered(item)),
        "acceptance_criteria_similar_pairs": similar_item_pairs(criteria),
        "task_groups_ready": {
            group: has_actionable_task(tasks.get(group), group=group)
            for group in ("be", "fe", "qa")
        },
        "definition_of_done_count": len(dod) if isinstance(dod, list) else 0,
        "context_sources_used": sorted(actual_sources),
        "expected_sources": sorted(expected_sources),
        "context_source_hit": bool(expected_sources & actual_sources) if expected_sources else bool(actual_sources),
    }

    failures = list(issues)
    actual_status = metrics.get("planning_status", READY)

    if actual_status == READY:
        if metrics["acceptance_criteria_count"] < 3:
            failures.append("Planner quality gate requires at least 3 acceptance criteria.")
        if metrics["given_when_then_ordered_count"] < 3:
            failures.append("Planner quality gate requires 3 ordered Given/When/Then acceptance criteria.")
        if metrics["acceptance_criteria_similar_pairs"]:
            failures.append(
                f"Planner quality gate requires distinct acceptance criteria; similar pairs={metrics['acceptance_criteria_similar_pairs']}."
            )
        for group, ready in metrics["task_groups_ready"].items():
            if not ready:
                failures.append(f"Planner quality gate requires an actionable {group.upper()} task.")
        if metrics["definition_of_done_count"] < 4:
            failures.append("Planner quality gate requires at least 4 Definition of Done checks.")
    elif actual_status == NEEDS_CLARIFICATION:
        if len(story.get("clarification_questions", [])) < 3:
            failures.append("Planner quality gate requires at least 3 clarification questions for ambiguous requests.")
    elif actual_status in {NEEDS_SPLIT, SPLIT_RECOMMENDED}:
        if not story.get("story_splits"):
            failures.append("Planner quality gate requires story_splits for oversized requests.")

    return {
        "agent": "planner",
        "passed": not failures,
        "metrics": metrics,
        "failures": list(dict.fromkeys(failures)),
    }


def _result(story: dict[str, Any], issues: list[str], warnings: list[str], normalized_status: str) -> dict[str, Any]:
    unique = list(dict.fromkeys(issues))
    normalized_story = copy.deepcopy(story)
    normalized_story["planning_status"] = normalized_status
    return {
        "passed": not unique,
        "issues": unique,
        "warnings": list(dict.fromkeys(warnings)),
        "normalized_story": normalized_story,
        "normalized_planning_status": normalized_status,
    }


def _required_context_issues(context: dict[str, Any]) -> list[str]:
    return [
        f"Missing required context source '{source}'."
        for source in context.get("missing_required_sources", [])
    ]


def _optional_context_warnings(context: dict[str, Any]) -> list[str]:
    return [
        f"Optional context source '{source}' was not retrieved."
        for source in context.get("missing_optional_sources", [])
    ]


def _required_concept_issues(story: dict[str, Any], route: dict[str, Any]) -> list[str]:
    text = _story_text(story)
    issues = []
    profile = route.get("profile", route)
    for concept in profile.get("required_concepts", route.get("required_concepts", [])):
        terms = CONCEPT_TERMS.get(concept, ())
        if terms and not any(term in text for term in terms):
            issues.append(f"Missing required concept '{concept}' for template '{route.get('template_name', '')}'.")
    return issues


def _forbidden_domain_issues(story: dict[str, Any], route: dict[str, Any]) -> list[str]:
    text = _story_text(story)
    issues = []
    profile = route.get("profile", route)
    for domain in profile.get("forbidden_domains", route.get("forbidden_domains", [])):
        if sum(1 for term in STRONG_DOMAIN_TERMS.get(domain, ()) if term in text) >= 2:
            issues.append(f"Output contains unrelated {domain} content for routed domain '{route.get('domain')}'.")
    return issues


def _ready_story_shape_issues(story: dict[str, Any]) -> list[str]:
    issues = []
    criteria = story.get("acceptance_criteria", [])
    if len(criteria) < 3:
        issues.append("READY stories require at least 3 acceptance criteria.")
    for index, criterion in enumerate(criteria, start=1):
        if not is_given_when_then_ordered(criterion):
            issues.append(f"Acceptance criterion #{index} must use Given / When / Then.")
    if story.get("story_points") not in FIBONACCI_POINTS:
        issues.append("Story points must be one of [1, 2, 3, 5, 8, 13].")
    tasks = story.get("tasks", {})
    for group in ("be", "fe", "qa"):
        values = tasks.get(group, []) if isinstance(tasks, dict) else []
        if not isinstance(values, list) or not values:
            issues.append(f"Tasks must include non-empty {group.upper()} items.")
            continue
        for item in values:
            if not isinstance(item, str) or len(item.split()) < 3:
                issues.append(f"{group.upper()} task must be concrete: {item!r}.")
            if is_user_story_task(item):
                issues.append(f"{group.upper()} task must not start with 'As a': {item}.")
            if is_placeholder_task(item):
                issues.append(f"{group.upper()} task is a placeholder: {item}.")
    return issues


def has_actionable_task(value: Any, group: str | None = None) -> bool:
    if not isinstance(value, list):
        return False
    return any(is_task_actionable_for_group(item, group) for item in value)


def is_task_actionable_for_group(value: Any, group: str | None = None) -> bool:
    if not isinstance(value, str) or len(value.strip().split()) < 3:
        return False
    if is_placeholder_task(value):
        return False
    if group not in TASK_REQUIRED_TERMS:
        return True
    lowered = value.lower()
    
    # Use word boundaries for forbidden terms to avoid Scunthorpe problem (e.g., "ui" in "build")
    def has_forbidden_term(text: str, term: str) -> bool:
        return bool(re.search(r'\b' + re.escape(term) + r'\b', text))

    if any(has_forbidden_term(lowered, term) for term in TASK_FORBIDDEN_TERMS[group]):
        return False
        
    # For required terms, substring matching is safer so we don't accidentally filter out valid tasks
    # like "selector" (matches "select"). If we don't find any, we still accept it if it's long enough
    # to be a descriptive task, to avoid throwing away good AI-generated tasks.
    has_required = any(term in lowered for term in TASK_REQUIRED_TERMS[group])
    
    # If it's a substantial task (e.g., > 5 words), we trust the AI even if it misses keywords
    if not has_required and len(value.split()) > 5:
        return True
        
    return has_required


def similar_item_pairs(values: Any, threshold: float = 0.62) -> list[str]:
    if not isinstance(values, list):
        return []
    pairs = []
    for left_index, left in enumerate(values):
        for right_index, right in enumerate(values[left_index + 1 :], start=left_index + 2):
            if item_similarity(left, right) >= threshold:
                pairs.append(f"{left_index + 1}-{right_index}")
    return pairs


def item_similarity(left: Any, right: Any) -> float:
    left_tokens = business_tokens(left)
    right_tokens = business_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def business_tokens(value: Any) -> set[str]:
    if not isinstance(value, str):
        return set()
    return {
        token[:-1] if token.endswith("s") and len(token) > 4 else token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 2 and token not in SIMILARITY_STOPWORDS
    }


def _ambiguous_issues(story: dict[str, Any]) -> list[str]:
    issues = []
    if story.get("planning_status") != NEEDS_CLARIFICATION:
        issues.append("Ambiguous requests must use planning_status NEEDS_CLARIFICATION.")
    if story.get("user_story"):
        issues.append("Ambiguous requests must not include a user_story.")
    if story.get("acceptance_criteria"):
        issues.append("Ambiguous requests must not include acceptance_criteria.")
    if story.get("story_points") is not None:
        issues.append("Ambiguous requests must not include story_points.")
    tasks = story.get("tasks", {})
    if isinstance(tasks, dict) and any(tasks.get(group) for group in ("be", "fe", "qa")):
        issues.append("Ambiguous requests must not include implementation tasks.")
    if story.get("definition_of_done"):
        issues.append("Ambiguous requests must not include Definition of Done.")
    if len(story.get("clarification_questions", [])) < 3:
        issues.append("Ambiguous requests must include at least 3 clarification questions.")
    return issues


def _oversized_issues(story: dict[str, Any], requirement: str) -> list[str]:
    issues = []
    if story.get("planning_status") not in {NEEDS_SPLIT, SPLIT_RECOMMENDED}:
        issues.append("Oversized requests must use planning_status NEEDS_SPLIT or SPLIT_RECOMMENDED.")
    splits = story.get("story_splits", [])
    if not splits:
        issues.append("Oversized requests must include story_splits from named capabilities.")
        return issues
    capability_names = [item for item in SPLIT_CAPABILITIES if item in requirement.lower()]
    split_text = _story_text({"story_splits": splits})
    missing = [name for name in capability_names if name not in split_text]
    if len(splits) < min(3, len(capability_names)):
        issues.append("Oversized requests must split multiple named capabilities, not one generic parent story.")
    if missing and len(missing) == len(capability_names):
        issues.append("story_splits must be created from actual named capabilities in the requirement.")
    return issues


def _story_text(story: dict[str, Any]) -> str:
    values = []
    for field in (
        "title",
        "user_story",
        "acceptance_criteria",
        "tasks",
        "definition_of_done",
        "clarification_questions",
        "assumptions",
        "story_splits",
        "sprint_allocation",
    ):
        values.append(str(story.get(field, "")))
    return " ".join(values).lower()
