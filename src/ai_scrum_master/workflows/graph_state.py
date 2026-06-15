"""LangGraph pipeline state definition.

Single TypedDict that flows through every node in the graph.
Each node reads what it needs, writes what it produces.
"""
from __future__ import annotations

from typing import Any, Callable, TypedDict


class PipelineState(TypedDict, total=False):
    """Shared state passed between all graph nodes.

    Fields are grouped by lifecycle stage:
    - Input: set once at graph entry
    - Routing: set by route_requirement node
    - Agent outputs: set by researcher/planner/evaluator nodes
    - Control flow: managed by conditional edges
    - Output: set by finalize nodes
    """

    # ── Input (immutable after entry) ─────────────────────────
    requirement: str
    n_results: int
    allow_fallback_without_context: bool
    forced_context_docs: list[str] | None
    project_id: str | None
    progress_callback: Callable[[str, dict], None] | None

    # ── Routing ───────────────────────────────────────────────
    route: dict[str, Any]
    requirement_type: str

    # ── Agent outputs ─────────────────────────────────────────
    raw_context: dict[str, Any]
    context: dict[str, Any]
    story: dict[str, Any] | None
    evaluation: dict[str, Any] | None
    planner_quality: dict[str, Any] | None

    # ── Control flow ──────────────────────────────────────────
    iteration: int
    max_retries: int
    research_feedback: str | None

    # ── Output ────────────────────────────────────────────────
    actions: dict[str, Any]
    next_steps: list[str]
