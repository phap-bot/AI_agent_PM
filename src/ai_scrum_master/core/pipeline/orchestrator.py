from __future__ import annotations

from typing import Any, Callable

from ai_scrum_master.actions.jira import JiraTool
from ai_scrum_master.actions.slack import SlackTool
from ai_scrum_master.core.schemas.agent_schemas import EvaluationOutput, PlannerStoryOutput, ResearchContextOutput, dump_model
from ai_scrum_master.core.pipeline.finalizer import blocked_actions, finalize_generation
from ai_scrum_master.core.utils.logging import get_logger
from ai_scrum_master.core.pipeline.requirement_router import route_requirement
from ai_scrum_master.core.validation.story_validator import validate_post_generation

logger = get_logger(__name__)


def generate_story_pipeline(
    *,
    requirement: str,
    n_results: int = 5,
    allow_fallback_without_context: bool = False,
    forced_context_docs: list[str] | None = None,
    crewai_builder: Callable[..., Any] | None = None,
    progress_callback: Callable[[str, dict], None] | None = None,
    project_id: str | None = None,
) -> dict:
    # ── LangGraph pipeline ──
    from ai_scrum_master.workflows.graph_pipeline import run_graph_pipeline

    result = run_graph_pipeline(
        requirement=requirement,
        n_results=n_results,
        allow_fallback_without_context=allow_fallback_without_context,
        forced_context_docs=forced_context_docs,
        progress_callback=progress_callback,
        project_id=project_id,
    )

    from ai_scrum_master.core.utils.database import DatabaseManager
    DatabaseManager.save_history(requirement, result, project_id=project_id)

    return result

