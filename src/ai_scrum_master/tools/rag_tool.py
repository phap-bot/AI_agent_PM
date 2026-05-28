from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ai_scrum_master.core.config import get_settings
from ai_scrum_master.retrieval.vector_store import search_context


class RagSearchInput(BaseModel):
    query: str = Field(..., description="Search query for project documentation context.")
    n_results: int = Field(default=5, ge=1, le=20, description="Maximum number of context chunks to retrieve.")
    collection_name: str | None = Field(default=None, description="Optional Chroma collection override.")


try:
    from crewai.tools import BaseTool
except Exception:
    BaseTool = object


class ProjectContextRagTool(BaseTool):
    name: str = "project_context_rag_search"
    description: str = "Search the local project documentation vector store for requirement-relevant context."
    args_schema: type[BaseModel] = RagSearchInput

    def _run(self, query: str, n_results: int = 5, collection_name: str | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        return search_context(
            query=query,
            n_results=n_results,
            collection_name=collection_name or settings.context_collection,
        )
