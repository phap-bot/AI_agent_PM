from __future__ import annotations


def score_story_approval(result: dict) -> int:
    return 1 if result.get("status") == "APPROVED" else 0
