from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ai_scrum_master.core.config.settings import get_settings
from ai_scrum_master.retrieval.vector_store import search_context


class RagSearchInput(BaseModel):
    query: str = Field(..., description="Search query for project documentation context.")
    n_results: int = Field(default=5, ge=1, le=20, description="Maximum number of context chunks to retrieve.")


try:
    from crewai.tools import BaseTool
except Exception:
    BaseTool = object


class ProjectContextRagTool(BaseTool):
    name: str = "ai_scrum_master_context_search"
    description: str = "Search the canonical local AI Scrum Master documentation vector store for requirement-relevant context."
    args_schema: type[BaseModel] = RagSearchInput

    def _run(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        settings = get_settings()
        return search_context(
            query=query,
            n_results=n_results,
            collection_name=settings.context_collection,
        )
