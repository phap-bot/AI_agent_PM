from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from ai_scrum_master.core.config import get_settings
from ai_scrum_master.core.logging import get_logger

logger = get_logger(__name__)


def get_persist_directory() -> Path:
    return Path(get_settings().chroma_persist_dir).resolve()


def get_embedding_function() -> Any:
    from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

    settings = get_settings()
    return OllamaEmbeddingFunction(
        url=settings.ollama_base_url,
        model_name=settings.embedding_model,
    )


def get_chroma_client() -> Any:
    import chromadb

    persist_directory = get_persist_directory()
    persist_directory.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(persist_directory))


def get_collection(name: str | None = None) -> Any:
    settings = get_settings()
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name or settings.context_collection,
        embedding_function=get_embedding_function(),
    )


def upsert_documents(
    documents: Sequence[str],
    ids: Sequence[str],
    metadatas: Sequence[dict] | None = None,
    collection_name: str | None = None,
) -> None:
    collection = get_collection(collection_name)
    payload: dict[str, object] = {
        "documents": list(documents),
        "ids": list(ids),
    }
    if metadatas is not None:
        payload["metadatas"] = list(metadatas)
    collection.upsert(**payload)


def clear_collection(collection_name: str | None = None) -> None:
    collection = get_collection(collection_name)
    existing = collection.get(include=[])
    ids = existing.get("ids", []) if isinstance(existing, dict) else []
    if ids:
        collection.delete(ids=ids)


def add_documents(
    documents: Sequence[str],
    ids: Sequence[str],
    metadatas: Sequence[dict] | None = None,
    collection_name: str | None = None,
) -> None:
    upsert_documents(
        documents=documents,
        ids=ids,
        metadatas=metadatas,
        collection_name=collection_name,
    )


def query_documents(
    query: str,
    n_results: int = 5,
    collection_name: str | None = None,
) -> dict:
    collection = get_collection(collection_name)
    return collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )


def search_context(
    query: str,
    n_results: int = 5,
    collection_name: str | None = None,
) -> list[dict]:
    settings = get_settings()
    if settings.rag_backend.strip().lower() == "langchain":
        try:
            from ai_scrum_master.retrieval.rag import search_context_with_langchain

            return search_context_with_langchain(
                query=query,
                n_results=n_results,
                collection_name=collection_name,
            )
        except Exception as exc:
            if not settings.rag_fallback_to_direct_chroma:
                raise
            logger.warning(
                "LangChain RAG retrieval failed; falling back to direct Chroma query. reason=%s",
                exc,
            )

    result = query_documents(query=query, n_results=n_results, collection_name=collection_name)
    documents = _first_result_list(result, "documents")
    ids = _first_result_list(result, "ids")
    metadatas = _first_result_list(result, "metadatas")
    distances = _first_result_list(result, "distances")

    matches: list[dict] = []
    for index, document in enumerate(documents):
        distance = distances[index] if index < len(distances) else None
        matches.append(
            {
                "id": ids[index] if index < len(ids) else "",
                "document": document,
                "metadata": metadatas[index] if index < len(metadatas) and isinstance(metadatas[index], dict) else {},
                "distance": distance,
                "score": distance_to_score(distance),
            }
        )
    return matches


def _first_result_list(result: dict, key: str) -> list:
    values = result.get(key, [[]])
    if not values:
        return []
    first = values[0]
    return first if isinstance(first, list) else []


def distance_to_score(distance: float | None) -> float:
    if distance is None:
        return 0.0
    return round(max(0.0, 1.0 - min(float(distance), 2.0) / 2.0), 3)
