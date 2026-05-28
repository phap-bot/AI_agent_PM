from ai_scrum_master.core.quality_gate import (
    evaluate_retrieval_cases,
    evaluate_retrieved_matches,
    quality_gate_passed,
)


def match(source: str) -> dict:
    return {"metadata": {"source": source}, "document": source}


def test_evaluate_retrieved_matches_computes_ranking_metrics() -> None:
    result = evaluate_retrieved_matches(
        [match("checkout_context.md"), match("auth_context.md"), match("auth_context.md")],
        {"auth_context": 1.0},
        k=3,
    )

    assert result["hit_rate_at_k"] == 1.0
    assert result["recall_at_k"] == 1.0
    assert result["precision_at_k"] == 2 / 3
    assert result["mrr"] == 0.5
    assert 0.0 < result["ndcg_at_k"] < 1.0


def test_evaluate_retrieval_cases_aggregates_per_source_metrics() -> None:
    cases = [
        {"query": "google login", "expected_sources": ["auth_context"]},
        {"query": "retry checkout", "expected_sources": ["checkout_context"]},
    ]
    responses = {
        "google login": [match("auth_context.md"), match("checkout_context.md")],
        "retry checkout": [match("auth_context.md"), match("checkout_context.md")],
    }

    result = evaluate_retrieval_cases(cases, k=2, retriever=lambda query, _k: responses[query])

    assert result["aggregate"]["hit_rate_at_k"] == 1.0
    assert result["aggregate"]["recall_at_k"] == 1.0
    assert result["aggregate"]["precision_at_k"] == 0.5
    assert result["aggregate"]["mrr"] == 0.75
    assert result["per_source"]["auth_context"]["recall_at_k"] == 1.0
    assert result["per_source"]["checkout_context"]["recall_at_k"] == 1.0


def test_quality_gate_reports_failures() -> None:
    passed, failures = quality_gate_passed(
        {
            "hit_rate_at_k": 0.5,
            "recall_at_k": 0.4,
            "precision_at_k": 0.3,
            "mrr": 0.2,
            "ndcg_at_k": 0.1,
        }
    )

    assert passed is False
    assert len(failures) == 5
