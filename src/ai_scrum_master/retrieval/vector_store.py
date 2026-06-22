from __future__ import annotations

from typing import Any, Sequence

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from ai_scrum_master.core.config.settings import get_settings
from ai_scrum_master.core.utils.logging import get_logger

logger = get_logger(__name__)


def get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    if settings.qdrant_api_key:
        return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return QdrantClient(url=settings.qdrant_url)


def canonical_collection_name(collection_name: str | None = None) -> str:
    settings = get_settings()
    if collection_name and collection_name != settings.context_collection:
        logger.warning(
            "Ignoring non-canonical collection override requested=%s canonical=%s",
            collection_name,
            settings.context_collection,
        )
    return settings.context_collection


def _ensure_collection_exists(client: QdrantClient, collection_name: str, vector_size: int = 768) -> None:
    if not client.collection_exists(collection_name=collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=rest.VectorParams(
                size=vector_size,
                distance=rest.Distance.COSINE
            )
        )


def get_embedding_function() -> Any:
    from ai_scrum_master.retrieval.rag import build_embeddings
    return build_embeddings()


def upsert_documents(
    documents: Sequence[str],
    ids: Sequence[str],
    metadatas: Sequence[dict] | None = None,
    collection_name: str | None = None,
) -> None:
    client = get_qdrant_client()
    collection = canonical_collection_name(collection_name)
    embedder = get_embedding_function()
    
    if not documents:
        return
        
    # Process in batches to avoid Ollama memory crash
    BATCH_SIZE = 128
    documents_list = list(documents)
    ids_list = list(ids)
    metadatas_list = list(metadatas) if metadatas else [{}] * len(documents_list)
    
    # Ensure collection exists before we start
    # We do a dummy embed of first document just to get vector size
    logger.info("[EMBED] Waking up Ollama embedding model (this may take 5-15 seconds)...")
    sample_embedding = embedder.embed_query(documents_list[0])
    vector_size = len(sample_embedding)
    _ensure_collection_exists(client, collection, vector_size)

    for i in range(0, len(documents_list), BATCH_SIZE):
        batch_docs = documents_list[i:i + BATCH_SIZE]
        batch_ids = ids_list[i:i + BATCH_SIZE]
        batch_metas = metadatas_list[i:i + BATCH_SIZE]
        
        logger.info("[EMBED] Processing batch %d to %d...", i, i + len(batch_docs))
        batch_embeddings = embedder.embed_documents(batch_docs)
        
        points = []
        import uuid
        for j, doc in enumerate(batch_docs):
            payload = {"document": doc}
            if batch_metas[j]:
                payload.update(batch_metas[j])
                
            # Qdrant requires IDs to be UUID or uint64. Convert string ID to a deterministic UUID.
            original_id = str(batch_ids[j])
            qdrant_id = str(uuid.uuid5(uuid.NAMESPACE_OID, original_id))
            
            points.append(rest.PointStruct(
                id=qdrant_id,
                vector=batch_embeddings[j],
                payload=payload
            ))
        
        client.upsert(collection_name=collection, points=points, wait=False)


def clear_collection(collection_name: str | None = None) -> None:
    client = get_qdrant_client()
    collection = canonical_collection_name(collection_name)
    if client.collection_exists(collection_name=collection):
        client.delete_collection(collection_name=collection)


def delete_project_documents(project_id: str, collection_name: str | None = None) -> None:
    client = get_qdrant_client()
    collection = canonical_collection_name(collection_name)
    if client.collection_exists(collection_name=collection):
        client.delete(
            collection_name=collection,
            points_selector=rest.FilterSelector(
                filter=rest.Filter(
                    must=[rest.FieldCondition(key="project_id", match=rest.MatchValue(value=project_id))]
                )
            )
        )
        logger.info("[VECTOR_STORE] Deleted documents for project_id=%s from collection='%s'", project_id, collection)


def add_documents(
    documents: Sequence[str],
    ids: Sequence[str],
    metadatas: Sequence[dict] | None = None,
    collection_name: str | None = None,
) -> None:
    upsert_documents(documents, ids, metadatas, collection_name)


def query_documents(
    query: str,
    n_results: int = 20,
    collection_name: str | None = None,
    project_id: str | None = None,
) -> dict:
    from ai_scrum_master.retrieval.rag import compact_query_for_embedding
    
    client = get_qdrant_client()
    collection = canonical_collection_name(collection_name)
    if not client.collection_exists(collection_name=collection):
        return {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
        
    embedder = get_embedding_function()
    query_vector = embedder.embed_query(compact_query_for_embedding(query))
    
    search_result = client.query_points(
        collection_name=collection,
        query=query_vector,
        limit=n_results
    )
    
    docs, metas, distances, ids = [], [], [], []
    for hit in search_result.points:
        docs.append(hit.payload.get("document", ""))
        metas.append(hit.payload)
        distances.append(1.0 - hit.score)  # Convert cosine similarity to "distance" equivalent
        ids.append(hit.id)
        
    return {
        "documents": [docs],
        "metadatas": [metas],
        "distances": [distances],
        "ids": [ids]
    }


def search_context(
    query: str,
    n_results: int = 20,
    collection_name: str | None = None,
    project_id: str | None = None,
) -> list[dict]:
    settings = get_settings()
    fallback_from = ""
    if settings.rag_backend.strip().lower() == "langchain":
        try:
            from ai_scrum_master.retrieval.rag import compact_query_for_embedding, search_context_with_langchain

            return search_context_with_langchain(
                query=compact_query_for_embedding(query),
                n_results=n_results,
                collection_name=collection_name,
                project_id=project_id,
            )
        except Exception as exc:
            if not getattr(settings, 'rag_fallback_to_direct_qdrant', True):
                raise
            fallback_from = "langchain_qdrant"
            logger.warning(
                "rag_backend=langchain_qdrant fallback_backend=direct_qdrant reason=%s",
                exc,
            )

    result = query_documents(query=query, n_results=n_results, collection_name=collection_name, project_id=project_id)
    documents = _first_result_list(result, "documents")
    ids = _first_result_list(result, "ids")
    metadatas = _first_result_list(result, "metadatas")
    distances = _first_result_list(result, "distances")

    matches: list[dict] = []
    for index, document in enumerate(documents):
        distance = distances[index] if index < len(distances) else None
        metadata = metadatas[index] if index < len(metadatas) and isinstance(metadatas[index], dict) else {}
        match = {
            "id": ids[index] if index < len(ids) else "",
            "document": document,
            "metadata": metadata,
            "distance": distance,
            "score": distance_to_score(distance),
            "retriever": "direct_qdrant",
        }
        if fallback_from:
            match["fallback_from"] = fallback_from
            metadata.setdefault("retriever", "direct_qdrant")
            metadata.setdefault("fallback_from", fallback_from)
        matches.append(match)
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


def get_chunks_by_filenames(
    filenames: list[str],
    query: str | None = None,
    n_results: int = 20,
    collection_name: str | None = None,
    project_id: str | None = None,
) -> list[dict]:
    """Retrieve chunks belonging to the given filenames from Qdrant.

    If query is provided, performs a semantic search filtered by filenames to get
    the most relevant chunks, preventing context window overflow. Results are
    always returned with score=1.0 so they bypass any downstream relevance filters.
    """
    if not filenames:
        return []

    client = get_qdrant_client()
    collection = canonical_collection_name(collection_name)
    if not client.collection_exists(collection_name=collection):
        logger.warning("[FORCED] Collection '%s' does not exist yet", collection)
        return []

    # Build an OR filter across all requested filenames
    should_conditions = [
        rest.FieldCondition(key="file_name", match=rest.MatchValue(value=fname))
        for fname in filenames
    ]
    
    query_filter = rest.Filter(should=should_conditions)
    all_matches: list[dict] = []

    if query:
        logger.info("[FORCED] Searching within filenames=%s for top %d chunks", filenames, n_results)
        embedder = get_embedding_function()
        from ai_scrum_master.retrieval.rag import compact_query_for_embedding
        query_vector = embedder.embed_query(compact_query_for_embedding(query))
        
        search_result = client.query_points(
            collection_name=collection,
            query=query_vector,
            query_filter=query_filter,
            limit=n_results
        )
        for hit in search_result.points:
            payload = hit.payload or {}
            all_matches.append({
                "id": hit.id,
                "document": payload.get("document", ""),
                "metadata": {k: v for k, v in payload.items() if k != "document"},
                "distance": 0.0,
                "score": 1.0,
                "retriever": "forced_context",
            })
        return all_matches
    offset = None
    while True:
        records, next_offset = client.scroll(
            collection_name=collection,
            scroll_filter=query_filter,
            limit=100,
            with_payload=True,
            with_vectors=False,
            offset=offset,
        )
        for record in records:
            payload = record.payload or {}
            all_matches.append({
                "id": record.id,
                "document": payload.get("document", ""),
                "metadata": {k: v for k, v in payload.items() if k != "document"},
                "distance": 0.0,
                "score": 1.0,
                "retriever": "forced_context",
            })
        if next_offset is None:
            break
        offset = next_offset

    logger.info(
        "[FORCED] Retrieved %d chunks for filenames=%s from collection '%s'",
        len(all_matches), filenames, collection,
    )
    return all_matches
