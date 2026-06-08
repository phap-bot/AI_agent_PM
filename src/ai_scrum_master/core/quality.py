from __future__ import annotations

import json
import re
from typing import Any

from ai_scrum_master.core.domain_profiles import (
    AMBIGUOUS_REQUEST,
    DOMAIN_KEYWORDS,
    DOMAIN_SOURCE_TERMS,
    OVERSIZED_CAPABILITIES,
    OVERSIZED_REQUEST,
    PROCESS_IMPROVEMENT,
    SOFTWARE_FEATURE,
    STRONG_DOMAIN_TERMS,
)

FIBONACCI_POINTS = {1, 2, 3, 5, 8, 13}
READY = "READY"
NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
SPLIT_RECOMMENDED = "SPLIT_RECOMMENDED"
NEEDS_SPLIT = "NEEDS_SPLIT"
REVISION = "REVISION"

PLACEHOLDER_TASKS = {
    "define backend changes",
    "define ui or client impact",
    "prepare validation scenarios",
}

GENERIC_AC_PHRASES = (
    "requirement is approved",
    "story is documented clearly",
    "acceptance criteria are checked",
    "tasks are assigned",
    "at least 3 criteria are present",
    "documented failure condition",
    "documented flow",
    "according to the retrieved context",
    "requested capability",
    "business outcome is observable",
)

GENERIC_TASK_PHRASES = (
    "backend logic",
    "frontend functionality",
    "functionality correctly",
    "documented backend/api behavior",
    "documented frontend/client behavior",
    "documented happy path",
    "happy path, failure paths, and edge cases",
    "requested capability",
    "business outcome",
)

def classify_requirement(requirement: str) -> str:
    text = requirement.lower().strip()
    words = text.split()
    oversized_hits = [capability for capability in OVERSIZED_CAPABILITIES if capability in text]
    if len(oversized_hits) >= 2:
        return OVERSIZED_REQUEST
    if has_domain(text, "scrum"):
        return PROCESS_IMPROVEMENT
    if len(words) <= 1 or (_starts_with_ambiguous_verb(text) and len(words) <= 4):
        return AMBIGUOUS_REQUEST
    if has_domain(text, "auth") or has_domain(text, "checkout") or has_domain(text, "notification"):
        return SOFTWARE_FEATURE
    if len(words) <= 3 or _starts_with_ambiguous_verb(text):
        return AMBIGUOUS_REQUEST
    return SOFTWARE_FEATURE


def requirement_domain(requirement: str) -> str:
    text = requirement.lower()
    for domain in ("auth", "checkout", "notification", "scrum"):
        if has_domain(text, domain):
            return domain
    return "general"


def has_domain(text: str, domain: str) -> bool:
    return any(keyword in text for keyword in DOMAIN_KEYWORDS[domain])


def filter_context_sources_for_requirement(requirement: str, sources: list[dict]) -> tuple[list[dict], list[dict]]:
    text = requirement.lower()
    domain = requirement_domain(requirement)
    if classify_requirement(requirement) == OVERSIZED_REQUEST:
        selected_domains = {candidate for candidate in ("auth", "checkout", "notification", "scrum") if has_domain(text, candidate)}
        selected_domains.add("scrum")
    elif domain == "general":
        return sources, []
    else:
        selected_domains = {domain}

    selected = []
    ignored = []
    for source in sources:
        source_text = f"{source.get('source', '')} {source.get('excerpt', '')}".lower()
        source_domains = {candidate for candidate in ("auth", "checkout", "notification", "scrum") if _context_matches_domain(source_text, candidate)}
        if source_domains & selected_domains:
            selected.append(source)
        else:
            ignored.append(source)
    return selected, ignored


def _context_matches_domain(source_text: str, domain: str) -> bool:
    return any(term in source_text for term in DOMAIN_SOURCE_TERMS[domain]) or has_domain(source_text, domain)


def validate_story_against_requirement(requirement: str, story: dict | None) -> list[str]:
    if story is None:
        return []
    issues: list[str] = []
    expected_type = classify_requirement(requirement)
    actual_type = story.get("story_type", SOFTWARE_FEATURE)
    if actual_type != expected_type:
        issues.append(f"story_type '{actual_type}' does not match current requirement domain '{expected_type}'.")

    issues.extend(domain_contamination_issues(requirement, story))
    issues.extend(_acceptance_criteria_issues(story))
    issues.extend(_task_issues(story))
    issues.extend(_ready_story_issues(story))
    issues.extend(_oversized_issues(expected_type, story))
    issues.extend(_ambiguous_issues(expected_type, story))
    return issues


def has_domain_contamination(requirement: str, value: Any) -> bool:
    return bool(domain_contamination_issues(requirement, {"value": value}))


def filter_domain_contaminated_items(requirement: str, items: list[Any]) -> tuple[list[Any], list[Any]]:
    kept = []
    removed = []
    for item in items:
        if has_domain_contamination(requirement, item):
            removed.append(item)
        else:
            kept.append(item)
    return kept, removed


def domain_contamination_issues(requirement: str, story: dict) -> list[str]:
    requirement_text = requirement.lower()
    story_text = json.dumps(_domain_validation_payload(story), ensure_ascii=False).lower()
    domain = requirement_domain(requirement)
    issues: list[str] = []
    if domain == "general":
        issues.extend(_general_domain_contamination_issues(story_text))
        return list(dict.fromkeys(issues))
    contamination = {
        "auth": ("scrum", "checkout", "notification"),
        "scrum": ("auth", "checkout", "notification"),
        "checkout": ("scrum", "auth", "notification"),
        "notification": ("checkout", "auth", "scrum"),
    }
    issue_messages = {
        ("auth", "scrum"): "Output contains unrelated Sprint Planning content for an authentication requirement.",
        ("scrum", "auth"): "Output contains unrelated authentication content for a Sprint Planning requirement.",
        ("checkout", "scrum"): "Output contains unrelated Sprint Planning content for a checkout requirement.",
        ("checkout", "auth"): "Output contains unrelated authentication content for a checkout requirement.",
        ("notification", "checkout"): "Output contains unrelated checkout content for a notification requirement.",
        ("notification", "auth"): "Output contains unrelated authentication content for a notification requirement.",
        ("notification", "scrum"): "Output contains unrelated Sprint Planning content for a notification requirement.",
    }
    for other_domain in contamination.get(domain, ()):
        if not has_domain(requirement_text, other_domain) and _has_strong_domain_contamination(story_text, other_domain):
            if domain == "auth" and other_domain == "notification" and _auth_email_reference_is_allowed(story_text):
                continue
            issues.append(issue_messages.get((domain, other_domain), f"Output contains unrelated {other_domain} content for current requirement."))
    return list(dict.fromkeys(issues))


def _general_domain_contamination_issues(story_text: str) -> list[str]:
    # Disabled for dynamic RAG support: general requirements can contain any domain
    return []


def _has_strong_domain_contamination(story_text: str, domain: str) -> bool:
    hits = sum(1 for term in STRONG_DOMAIN_TERMS.get(domain, ()) if term in story_text)
    if domain == "checkout":
        return hits >= 2
    if domain == "scrum":
        return hits >= 1
    if domain == "notification":
        return hits >= 1
    if domain == "auth":
        return hits >= 2
    return False


def _auth_email_reference_is_allowed(story_text: str) -> bool:
    notification_terms = ("slack", "webhook", "notification", "alert", "jira notification", "in-app notification")
    return "email" in story_text and not any(term in story_text for term in notification_terms)


def is_user_story_task(item: Any) -> bool:
    if not isinstance(item, str):
        return False
    lowered = item.strip().lower()
    return lowered.startswith("as a") or " i want " in f" {lowered} "


def is_generic_acceptance_criterion(criterion: Any) -> bool:
    if not isinstance(criterion, str):
        return False
    lowered = criterion.lower()
    return any(phrase in lowered for phrase in GENERIC_AC_PHRASES)


def is_placeholder_task(item: Any) -> bool:
    if not isinstance(item, str):
        return False
    lowered = item.strip().lower()
    return lowered in PLACEHOLDER_TASKS or any(phrase in lowered for phrase in GENERIC_TASK_PHRASES)


def is_given_when_then_ordered(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    matches = [re.search(rf"\b{token}\b", value, flags=re.IGNORECASE) for token in ("given", "when", "then")]
    return all(matches) and matches[0].start() < matches[1].start() < matches[2].start()


def _acceptance_criteria_issues(story: dict) -> list[str]:
    issues = []
    for index, criterion in enumerate(story.get("acceptance_criteria", []), start=1):
        if is_generic_acceptance_criterion(criterion):
            issues.append(f"Acceptance criterion #{index} is generic template text and must be business-specific.")
    return issues


def _domain_validation_payload(story: dict) -> dict:
    user_facing_fields = (
        "title",
        "user_story",
        "acceptance_criteria",
        "tasks",
        "definition_of_done",
        "clarification_questions",
        "assumptions",
        "story_splits",
        "sprint_allocation",
        "context_sources",
        "value",
    )
    return {field: story.get(field) for field in user_facing_fields if field in story}


def _task_issues(story: dict) -> list[str]:
    if story.get("planning_status", READY) != READY:
        return []
    issues = []
    tasks = story.get("tasks", {})
    for key in ("be", "fe", "qa"):
        group = tasks.get(key, []) if isinstance(tasks, dict) else []
        if not group:
            issues.append(f"Tasks must include at least one actionable {key.upper()} item.")
        for item in group if isinstance(group, list) else []:
            if is_user_story_task(item):
                issues.append(f"Tasks must be concrete actions, not user stories: {key.upper()} item '{item}'.")
            if is_placeholder_task(item):
                issues.append(f"Tasks must not use generic placeholder task: {item}.")
    return issues


def _ready_story_issues(story: dict) -> list[str]:
    if story.get("planning_status", READY) != READY:
        return []
    issues = []
    if len(story.get("acceptance_criteria", [])) < 3:
        issues.append("At least 3 acceptance criteria are required.")
    for index, criterion in enumerate(story.get("acceptance_criteria", []), start=1):
        if not is_given_when_then_ordered(criterion):
            issues.append(f"Acceptance criterion #{index} must use Given / When / Then.")
    if story.get("story_points") not in FIBONACCI_POINTS:
        issues.append("Story points must use Fibonacci values.")
    return issues


def _oversized_issues(expected_type: str, story: dict) -> list[str]:
    if expected_type != OVERSIZED_REQUEST:
        return []
    issues = []
    if story.get("planning_status") not in {NEEDS_SPLIT, SPLIT_RECOMMENDED}:
        issues.append("Oversized requests must use NEEDS_SPLIT or SPLIT_RECOMMENDED planning_status.")
    if not story.get("story_splits"):
        issues.append("Oversized requests must include story_splits.")
    return issues


def _ambiguous_issues(expected_type: str, story: dict) -> list[str]:
    if expected_type != AMBIGUOUS_REQUEST:
        return []
    issues = []
    if story.get("planning_status") != NEEDS_CLARIFICATION:
        issues.append("Ambiguous requests must use NEEDS_CLARIFICATION planning_status.")
    if len(story.get("clarification_questions", [])) < 3:
        issues.append("Ambiguous requests must include at least 3 clarification questions.")
    return issues


def _starts_with_ambiguous_verb(text: str) -> bool:
    ambiguous_terms = ("improve", "optimize", "enhance", "fix", "update", "better")
    return any(text == term or text.startswith(f"{term} ") for term in ambiguous_terms)
