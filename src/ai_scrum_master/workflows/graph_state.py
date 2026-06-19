from typing import Any, TypedDict

class PipelineState(TypedDict, total=False):
    requirement: str
    n_results: int
    allow_fallback_without_context: bool
    forced_context_docs: list[str] | None
    project_id: str | None
    progress_callback: Any
    iteration: int
    max_retries: int
    research_feedback: str | None
    route: dict[str, Any]
    requirement_type: str
    tech_classification: dict[str, Any]
    raw_context: dict[str, Any]
    context: dict[str, Any]
    story: dict[str, Any] | None
    evaluation: dict[str, Any] | None
    planner_quality: dict[str, Any] | None
    actions: dict[str, Any]
    next_steps: list[str]
