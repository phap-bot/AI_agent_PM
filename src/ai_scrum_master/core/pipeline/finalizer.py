from __future__ import annotations

from typing import Any

READY = "READY"
APPROVED = "APPROVED"
REVISION = "REVISION"
ACTION_BLOCK_WARNING = "Action blocked until evaluator returns APPROVED and planning_status is READY."


def finalize_generation(story: dict[str, Any] | None, evaluation: dict[str, Any]) -> dict[str, Any]:
    normalized_evaluation = dict(evaluation)
    planning_status = story.get("planning_status", READY) if isinstance(story, dict) else None

    if normalized_evaluation.get("status") == APPROVED and planning_status != READY:
        issue = "Story is not READY, so evaluator status cannot be APPROVED."
        normalized_evaluation = _revision_with_issue(normalized_evaluation, issue)

    actions_ready = actions_are_ready(story, normalized_evaluation)
    return {
        "evaluation": normalized_evaluation,
        "actions_ready": actions_ready,
        "actions": {} if actions_ready else blocked_actions(),
    }


def actions_are_ready(story: dict[str, Any] | None, evaluation: dict[str, Any]) -> bool:
    return (
        isinstance(story, dict)
        and story.get("planning_status", READY) == READY
        and evaluation.get("status") == APPROVED
    )


def should_block_planning(context: dict[str, Any], allow_fallback_without_context: bool) -> bool:
    if allow_fallback_without_context:
        return False
        
    # Allow oversized requests to proceed to planning so that the planner can suggest splits,
    # even if no relevant context was found.
    route = context.get("route", {})
    if route.get("story_type") == "oversized_request":
        return False
        
    if context.get("missing_required_sources"):
        return True
    if context.get("retrieval_status") in {"empty", "no_relevant_context", "failed"}:
        return True

    quality_gate = context.get("quality_gate")
    return isinstance(quality_gate, dict) and quality_gate.get("passed") is False


def blocked_actions(warning: str = ACTION_BLOCK_WARNING) -> dict[str, dict[str, Any]]:
    return {
        "jira": {"ready": False, "payload": None, "warnings": [warning]},
        "slack": {"ready": False, "payload": None, "warnings": [warning]},
    }


def _revision_with_issue(evaluation: dict[str, Any], issue: str) -> dict[str, Any]:
    return {
        "status": REVISION,
        "issues": list(dict.fromkeys(evaluation.get("issues", []) + [issue])),
        "revision_instructions": list(dict.fromkeys(evaluation.get("revision_instructions", []) + [issue])),
        "dod_score": evaluation.get("dod_score", {}),
        "warnings": evaluation.get("warnings", []),
    }
