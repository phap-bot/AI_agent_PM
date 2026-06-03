from ai_scrum_master.retrieval.rag import citation_id_for_match
from ai_scrum_master.retrieval import vector_store
from ai_scrum_master.retrieval.vector_store import canonical_collection_name, distance_to_score


def test_retrieval_modules_live_outside_core() -> None:
    assert distance_to_score(0.0) == 1.0
    assert citation_id_for_match({"metadata": {"source": "auth_context.md", "chunk_index": 0}}) == "auth_context.md#chunk-0"


def test_collection_override_resolves_to_canonical_collection(monkeypatch) -> None:
    monkeypatch.setenv("CHROMA_COLLECTION", "ai_scrum_master_context")

    assert canonical_collection_name() == "ai_scrum_master_context"
    assert canonical_collection_name("legacy_context") == "ai_scrum_master_context"


def test_langchain_fallback_logs_normalized_backend_and_tags_matches(monkeypatch) -> None:
    monkeypatch.setenv("RAG_BACKEND", "langchain")
    monkeypatch.setenv("RAG_FALLBACK_TO_DIRECT_CHROMA", "true")

    def broken_langchain_search(*args, **kwargs):
        raise RuntimeError("langchain_chroma unavailable")

    def fake_query_documents(*args, **kwargs):
        return {
            "documents": [["Auth stack uses Google OAuth."]],
            "ids": [["auth-0"]],
            "metadatas": [[{"source": "auth.md", "chunk_index": 0}]],
            "distances": [[0.2]],
        }

    monkeypatch.setattr(vector_store, "query_documents", fake_query_documents)
    monkeypatch.setattr(
        "ai_scrum_master.retrieval.rag.search_context_with_langchain",
        broken_langchain_search,
    )

    captured_warnings = []
    monkeypatch.setattr(
        vector_store.logger,
        "warning",
        lambda message, *args: captured_warnings.append(message % args),
    )

    matches = vector_store.search_context("Add Google login", n_results=1)

    assert captured_warnings == [
        "rag_backend=langchain_chroma fallback_backend=direct_chroma reason=langchain_chroma unavailable"
    ]
    assert matches[0]["retriever"] == "direct_chroma"
    assert matches[0]["fallback_from"] == "langchain_chroma"
    assert matches[0]["metadata"]["retriever"] == "direct_chroma"
    assert matches[0]["metadata"]["fallback_from"] == "langchain_chroma"


def test_langchain_fallback_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setenv("RAG_BACKEND", "langchain")
    monkeypatch.setenv("RAG_FALLBACK_TO_DIRECT_CHROMA", "false")

    def broken_langchain_search(*args, **kwargs):
        raise RuntimeError("langchain_chroma unavailable")

    monkeypatch.setattr(
        "ai_scrum_master.retrieval.rag.search_context_with_langchain",
        broken_langchain_search,
    )

    try:
        vector_store.search_context("Add Google login", n_results=1)
    except RuntimeError as exc:
        assert str(exc) == "langchain_chroma unavailable"
    else:
        raise AssertionError("Expected disabled fallback to re-raise LangChain retrieval failure")
