from __future__ import annotations

from ai_scrum_master.core.config import AgentProfileConfig, get_settings
from ai_scrum_master.core.logging import get_logger
from ai_scrum_master.core.vector_store import query_documents

logger = get_logger(__name__)


class ResearcherAgent:
    def __init__(self, profile: AgentProfileConfig | None = None) -> None:
        self.settings = get_settings()
        self.profile = profile

    def run(self, requirement: str, n_results: int = 5) -> dict:
        logger.info(
            "Research query started collection=%s n_results=%s requirement_length=%s",
            self.settings.context_collection,
            n_results,
            len(requirement),
        )
        try:
            result = query_documents(
                query=requirement,
                n_results=n_results,
                collection_name=self.settings.context_collection,
            )
        except Exception as exc:
            logger.exception("Research query failed; continuing with empty context")
            return {
                "documents": [],
                "ids": [],
                "metadatas": [],
                "distances": [],
                "confidence": 0.0,
                "warnings": [
                    f"Context retrieval failed; planner should continue with explicit assumptions. Reason: {exc}"
                ],
            }

        documents = self._first_result_list(result, "documents")
        ids = self._first_result_list(result, "ids")
        metadatas = self._first_result_list(result, "metadatas")
        distances = self._first_result_list(result, "distances")
        warnings: list[str] = []

        if not documents:
            warnings.append("No relevant project context found in ChromaDB.")

        confidence = self._estimate_confidence(distances, has_documents=bool(documents))
        if confidence < 0.5:
            warnings.append("Retrieved context confidence is low; planner should state assumptions explicitly.")

        logger.info(
            "Research query completed documents=%s confidence=%s warnings=%s",
            len(documents),
            confidence,
            len(warnings),
        )
        return {
            "documents": documents,
            "ids": ids,
            "metadatas": metadatas,
            "distances": distances,
            "confidence": confidence,
            "warnings": warnings,
        }

    def _first_result_list(self, result: dict, key: str) -> list:
        values = result.get(key, [[]])
        if not values:
            return []
        first = values[0]
        return first if isinstance(first, list) else []

    def _estimate_confidence(self, distances: list[float], has_documents: bool) -> float:
        if not has_documents:
            return 0.0
        if not distances:
            return 0.5

        best_distance = min(distances)
        if best_distance <= 0.35:
            return 0.9
        if best_distance <= 0.75:
            return 0.7
        if best_distance <= 1.2:
            return 0.5
        return 0.3
