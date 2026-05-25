from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from ai_scrum_master.core.config import get_settings


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


def add_documents(
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
    collection.add(**payload)


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
