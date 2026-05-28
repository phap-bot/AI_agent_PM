from ai_scrum_master.core.quality_gate import (
    evaluate_retrieved_matches,
    normalize_source_name,
    quality_gate_passed,
)


def test_quality_gate_is_canonical_retrieval_quality_module() -> None:
    matches = [
        {"metadata": {"source": "auth_context.md"}},
        {"metadata": {"source": "checkout_context.md"}},
    ]

    metrics = evaluate_retrieved_matches(matches, {"auth_context": 1.0}, k=2)
    passed, failures = quality_gate_passed(metrics, min_hit_rate=1.0, min_recall=1.0, min_precision=0.5)

    assert normalize_source_name("docs/auth_context.md") == "auth_context"
    assert metrics["hit_rate_at_k"] == 1.0
    assert passed is True
    assert failures == []
