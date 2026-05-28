from ai_scrum_master.retrieval.rag import citation_id_for_match
from ai_scrum_master.retrieval.vector_store import distance_to_score


def test_retrieval_modules_live_outside_core() -> None:
    assert distance_to_score(0.0) == 1.0
    assert citation_id_for_match({"metadata": {"source": "auth_context.md", "chunk_index": 0}}) == "auth_context.md#chunk-0"
