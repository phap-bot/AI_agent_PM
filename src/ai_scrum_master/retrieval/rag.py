from __future__ import annotations

import json
import re
from importlib import import_module
from pathlib import Path
from typing import Any

from ai_scrum_master.core.config.settings import get_settings
from ai_scrum_master.core.utils.logging import get_logger
from ai_scrum_master.core.llm.prompts import render_prompt
from ai_scrum_master.retrieval.vector_store import canonical_collection_name

logger = get_logger(__name__)

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "be",
    "can",
    "do",
    "does",
    "for",
    "how",
    "in",
    "is",
    "of",
    "should",
    "the",
    "to",
    "what",
    "who",
}

LANGCHAIN_INSTALL_HINT = (
    "Install RAG dependencies with: "
    "pip install langchain langchain-community langchain-chroma "
    "langchain-ollama langchain-text-splitters"
)

DEFAULT_EMBEDDING_QUERY_CHARS = 3000



class LangChainRagDependencyError(ImportError):
    pass


def _load_attr(module_name: str, attr_name: str) -> Any:
    try:
        module = import_module(module_name)
    except ImportError as exc:
        raise LangChainRagDependencyError(
            f"Missing LangChain dependency '{module_name}'"
        ) from exc
    return getattr(module, attr_name)


from functools import lru_cache

@lru_cache(maxsize=1)
def build_embeddings() -> Any:
    settings = get_settings()
    OllamaEmbeddings = _load_attr("langchain_ollama", "OllamaEmbeddings")
    logger.info(f"Using OllamaEmbeddings with model: {settings.embedding_model}")
    underlying_embeddings = OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_base_url,
        keep_alive="0",  # Unload immediately to save VRAM
    )
    
    try:
        CacheBackedEmbeddings = _load_attr("langchain.embeddings", "CacheBackedEmbeddings")
        LocalFileStore = _load_attr("langchain_community.storage", "LocalFileStore")
        
        cache_dir = Path(".cache/embeddings")
        cache_dir.mkdir(parents=True, exist_ok=True)
        store = LocalFileStore(str(cache_dir))
        
        cached_embedder = CacheBackedEmbeddings.from_bytes_store(
            underlying_embeddings, store, namespace=settings.embedding_model
        )
        logger.info("Enabled CacheBackedEmbeddings (LocalFileStore) for vector caching.")
        return cached_embedder
    except Exception as e:
        logger.warning(f"Could not enable embedding cache: {e}")
        return underlying_embeddings


def build_chat_ollama(**overrides: Any) -> Any:
    ChatOllama = _load_attr("langchain_ollama", "ChatOllama")
    settings = get_settings()
    options = {
        "model": settings.reasoning_model,
        "base_url": settings.ollama_base_url,
        "temperature": 0.0,
        "num_ctx": settings.ollama_num_ctx,
        "num_gpu": settings.ollama_num_gpu,
        "keep_alive": "0",  # Unload immediately to save VRAM
    }
    options.update(overrides)
    return ChatOllama(**options)


def build_qdrant_vector_store(collection_name: str | None = None) -> Any:
    QdrantVectorStore = _load_attr("langchain_qdrant", "QdrantVectorStore")
    settings = get_settings()
    
    from qdrant_client import QdrantClient
    if settings.qdrant_api_key:
        client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    else:
        client = QdrantClient(url=settings.qdrant_url)
        
    return QdrantVectorStore(
        client=client,
        collection_name=canonical_collection_name(collection_name),
        embedding=build_embeddings()
    )


def search_context_with_langchain(
    query: str,
    n_results: int = 5,
    collection_name: str | None = None,
    project_id: str | None = None,
) -> list[dict[str, Any]]:
    settings = get_settings()
    retrieval_query = compact_query_for_embedding(query)
    vector_store = build_qdrant_vector_store(collection_name)
    fetch_k = max(n_results, settings.rag_vector_fetch_k if settings.rag_hybrid_search else n_results)
    
    search_kwargs = {}
    results = vector_store.similarity_search_with_score(retrieval_query, k=fetch_k, **search_kwargs)

    matches: list[dict[str, Any]] = []
    for document, distance in results:
        metadata = dict(document.metadata or {})
        chunk_id = str(metadata.get("chunk_id") or metadata.get("id") or "")
        matches.append(
            {
                "id": chunk_id,
                "document": document.page_content,
                "metadata": metadata,
                "distance": float(distance) if distance is not None else None,
                "score": distance_to_score(float(distance) if distance is not None else None),
                "vector_score": distance_to_score(float(distance) if distance is not None else None),
                "lexical_score": lexical_score(query, document.page_content, metadata),
                "retriever": "langchain_qdrant",
            }
        )
    if settings.rag_hybrid_search:
        matches = merge_lexical_candidates(retrieval_query, matches, vector_store)
        matches = rerank_hybrid_matches(matches)
    return matches[:n_results]


def compact_query_for_embedding(query: str, max_chars: int = DEFAULT_EMBEDDING_QUERY_CHARS) -> str:
    normalized = normalize_for_search_input(query)
    if len(normalized) <= max_chars:
        return normalized

    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    title = lines[0] if lines else normalized[:200]
    section_heads = ("### description", "### expected behavior", "### actual behavior", "### steps to reproduce")
    selected = [title]
    lowered_lines = [line.lower() for line in lines]
    for head in section_heads:
        for index, line in enumerate(lowered_lines):
            if line.startswith(head):
                selected.extend(lines[index : index + 2])
                break

    compacted = "\n".join(dict.fromkeys(selected)).strip()
    if len(compacted) < min(800, max_chars) and normalized:
        compacted = f"{compacted}\n\n{normalized[:max_chars]}".strip()
    return compacted[:max_chars]


def normalize_for_search_input(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def merge_lexical_candidates(query: str, matches: list[dict[str, Any]], vector_store: Any) -> list[dict[str, Any]]:
    by_id = {citation_id_for_match(match): match for match in matches}
    try:
        raw = vector_store.get(include=["documents", "metadatas"])
    except Exception as exc:
        logger.warning("LangChain lexical candidate fetch failed; using vector candidates only. reason=%s", exc)
        return matches

    ids = raw.get("ids", []) if isinstance(raw, dict) else []
    documents = raw.get("documents", []) if isinstance(raw, dict) else []
    metadatas = raw.get("metadatas", []) if isinstance(raw, dict) else []
    for index, document in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) and isinstance(metadatas[index], dict) else {}
        chunk_id = metadata.get("chunk_id") or metadata.get("id") or (ids[index] if index < len(ids) else "")
        candidate = {
            "id": str(chunk_id),
            "document": document,
            "metadata": metadata,
            "distance": None,
            "score": 0.0,
            "vector_score": 0.0,
            "lexical_score": lexical_score(query, str(document), metadata),
            "retriever": "langchain_chroma_hybrid",
        }
        if candidate["lexical_score"] <= 0:
            continue
        existing = by_id.get(citation_id_for_match(candidate))
        if existing:
            existing["lexical_score"] = max(float(existing.get("lexical_score") or 0.0), candidate["lexical_score"])
        else:
            by_id[citation_id_for_match(candidate)] = candidate
    return list(by_id.values())


def rerank_hybrid_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for match in matches:
        vector_score = float(match.get("vector_score") or 0.0)
        lexical = float(match.get("lexical_score") or 0.0)
        hybrid = (0.35 * vector_score) + (0.65 * lexical)
        if lexical >= 0.75:
            hybrid += 0.1
        rank_score = round(min(hybrid, 1.0), 3)
        match["rank_score"] = rank_score
        match["score"] = round(max(rank_score, vector_score if lexical >= 0.3 else rank_score), 3)
    return sorted(matches, key=lambda item: float(item.get("rank_score") or item.get("score") or 0.0), reverse=True)


def lexical_score(query: str, document: str, metadata: dict[str, Any]) -> float:
    query_tokens = content_tokens(query)
    if not query_tokens:
        return 0.0

    source = str(metadata.get("source") or metadata.get("file_name") or "")
    source_tokens = content_tokens(source.replace("_", " ").replace("-", " "))
    document_tokens = content_tokens(document[:2500])

    overlap_denominator = min(len(query_tokens), 5)
    source_overlap = min(1.0, len(query_tokens & source_tokens) / overlap_denominator)
    document_overlap = min(1.0, len(query_tokens & document_tokens) / overlap_denominator)
    phrase_bonus = phrase_match_bonus(query, document, source)
    source_bonus = 0.2 if source_overlap >= 0.3 else 0.0
    return round(min(1.0, (0.5 * source_overlap) + (0.3 * document_overlap) + phrase_bonus + source_bonus), 3)


def phrase_match_bonus(query: str, document: str, source: str) -> float:
    normalized_query = normalize_for_search(query)
    searchable = f"{normalize_for_search(source)} {normalize_for_search(document[:2500])}"
    bonus = 0.0
    if "acceptance criteria" in normalized_query and "acceptance criteria" in searchable:
        bonus += 0.2
    if (
        ("user story" in normalized_query or "user stories" in normalized_query)
        and ("user story" in searchable or "user stories" in searchable)
    ):
        bonus += 0.2
    if "definition of done" in normalized_query and "definition of done" in searchable:
        bonus += 0.2
    for phrase in ("google", "oauth", "callback", "jwt"):
        if phrase in normalized_query and phrase in searchable:
            bonus += 0.1
    for phrase in ("epic", "invest", "3 c", "three c"):
        if phrase in normalized_query and phrase in searchable:
            bonus += 0.2
    return min(bonus, 0.35)


def content_tokens(text: str) -> set[str]:
    return {
        stem_token(token)
        for token in re.findall(r"[a-z0-9]+", normalize_for_search(text))
        if len(token) > 1 and token not in STOPWORDS
    }


def normalize_for_search(text: str) -> str:
    return text.lower().replace("’", "'").replace("`", "'")


def stem_token(token: str) -> str:
    if token.endswith("ies") and len(token) > 4:
        return f"{token[:-3]}y"
    if token.endswith("s") and len(token) > 3:
        return token[:-1]
    return token


def add_langchain_documents(
    documents: list[Any],
    ids: list[str],
    collection_name: str | None = None,
) -> None:
    """Add documents with batch embedding for maximum speed using Qdrant."""
    if not documents:
        return

    import time
    t_start = time.time()

    from ai_scrum_master.retrieval.vector_store import upsert_documents
    
    texts = [str(doc.page_content) for doc in documents]
    metadatas = []
    for doc in documents:
        meta = dict(doc.metadata) if doc.metadata else {}
        clean_meta = {}
        for k, v in meta.items():
            if isinstance(v, (str, int, float, bool)):
                clean_meta[k] = v
            elif v is not None:
                clean_meta[k] = str(v)
        metadatas.append(clean_meta)

    t_upsert = time.time()
    upsert_documents(texts, ids, metadatas, collection_name)
    logger.info("[EMBED] Upserted %d chunks to Qdrant in %.2fs", len(ids), time.time() - t_upsert)
    logger.info("[EMBED] Total add_langchain_documents: %.2fs", time.time() - t_start)


def normalize_metadata(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}

def build_rag_context(matches: list[dict[str, Any]]) -> str:
    blocks: list[str] = []

    for index, match in enumerate(matches, start=1):
        metadata = normalize_metadata(match.get("metadata"))

        chunk_id = citation_id_for_match(match)

        source = (
            metadata.get("source")
            or metadata.get("file_name")
            or "unknown source"
        )

        chunk_index = metadata.get("chunk_index", "?")
        score = match.get("score", 0.0)
        content = str(match.get("document") or "").strip()

        blocks.append(
            f"[{index}] CITATION_ID: {chunk_id}\n"
            f"source={source} chunk={chunk_index} score={score}\n"
            f"{content}"
        )

    return "\n\n---\n\n".join(blocks)


def generate_answer_from_matches(question: str, matches: list[dict[str, Any]]) -> dict[str, Any]:
    if not matches:
        return {
            "status": "INSUFFICIENT_CONTEXT",
            "answer": "INSUFFICIENT_CONTEXT",
            "citations": [],
            "unsupported_claims": ["No retrieved source chunks were provided."],
        }

    ChatPromptTemplate = _load_attr("langchain_core.prompts", "ChatPromptTemplate")
    StrOutputParser = _load_attr("langchain_core.output_parsers", "StrOutputParser")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("user", "{user_prompt}"),
        ]
    )
    chain = prompt | build_chat_ollama() | StrOutputParser()
    raw_answer = chain.invoke({
        "user_prompt": render_prompt(
            "rag_answer.md",
            question=question,
            citation_ids="\n".join(f"- {citation_id_for_match(match)}" for match in matches),
            context=build_rag_context(matches),
        )
    })
    parsed = parse_json_object(raw_answer)
    parsed.setdefault("status", "ANSWERED")
    parsed.setdefault("answer", "")
    parsed.setdefault("citations", [])
    parsed.setdefault("unsupported_claims", [])
    parsed["citations"] = normalize_answer_citations(parsed.get("citations", []), matches)
    parsed["raw_response"] = raw_answer
    return parsed


def generate_grounded_answer(
    question: str,
    n_results: int = 3,
    collection_name: str | None = None,
) -> dict[str, Any]:
    matches = search_context_with_langchain(question, n_results=n_results, collection_name=collection_name)
    answer = generate_answer_from_matches(question, matches)
    answer["matches"] = matches
    return answer


def parse_json_object(text: str) -> dict[str, Any]:
    # Remove <think>...</think> blocks if present
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            value = json.loads(match.group(0))
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass

    return {
        "status": "UNPARSEABLE",
        "answer": "",
        "citations": [],
        "unsupported_claims": ["Model did not return valid JSON."],
    }


def citation_id_for_match(match: dict[str, Any]) -> str:
    raw_metadata = match.get("metadata")
    metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}

    match_id = match.get("id")
    if match_id:
        return str(match_id)

    chunk_id = metadata.get("chunk_id")
    if chunk_id:
        return str(chunk_id)

    source = metadata.get("source") or metadata.get("file_name") or "unknown"
    chunk_index = metadata.get("chunk_index", "?")

    return f"{source}#chunk-{chunk_index}"


def normalize_answer_citations(citations: Any, matches: list[dict[str, Any]]) -> list[str]:
    if not isinstance(citations, list):
        return []
    valid_ids = [citation_id_for_match(match) for match in matches]
    by_lower = {value.lower(): value for value in valid_ids}
    normalized = []
    for citation in citations:
        candidate = _normalize_citation_text(str(citation))
        resolved = by_lower.get(candidate.lower())
        if resolved is None:
            resolved = _resolve_chunk_id_suffix(candidate, valid_ids)
        if resolved and resolved not in normalized:
            normalized.append(resolved)
    return normalized


def _normalize_citation_text(citation: str) -> str:
    value = citation.strip().strip('"').strip("'")
    for prefix in ("chunk_id=", "chunk_id:", "CITATION_ID:", "citation_id:", "id="):
        if value.lower().startswith(prefix.lower()):
            value = value[len(prefix):].strip()
            break
    return value


def _resolve_chunk_id_suffix(candidate: str, valid_ids: list[str]) -> str | None:
    if candidate.lower() == "chunk_id":
        return None
    for prefix in ("chunk_id-", "citation_id-"):
        if candidate.lower().startswith(prefix):
            suffix = candidate[len(prefix) - 1 :]
            matches = [valid_id for valid_id in valid_ids if valid_id.endswith(suffix)]
            if len(matches) == 1:
                return matches[0]
    return None


def distance_to_score(distance: float | None) -> float:
    if distance is None:
        return 0.0
    return round(max(0.0, 1.0 - min(float(distance), 2.0) / 2.0), 3)
