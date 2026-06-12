import inspect

from ai_scrum_master.agents import researcher
from ai_scrum_master.agents.researcher import ResearcherAgent
from ai_scrum_master.core.config import Settings
from ai_scrum_master.core.domain_profiles import SOURCE_MATCH_TERMS


def test_researcher_source_matching_uses_central_domain_profile_terms() -> None:
    source = inspect.getsource(ResearcherAgent._match_matches_expected)

    assert "auth_context" in SOURCE_MATCH_TERMS
    assert "expected_terms =" not in source


def test_researcher_returns_empty_context_when_query_fails(monkeypatch) -> None:
    def broken_search_context(*args, **kwargs):
        raise RuntimeError("chroma unavailable")

    monkeypatch.setattr(researcher, "search_context", broken_search_context)

    result = ResearcherAgent().run("Add Google login")

    assert result["documents"] == []
    assert result["retrieval_status"] == "failed"
    assert result["confidence"] == 0.0
    assert result["latency_ms"] >= 0
    assert "researcher_ms" in result["stage_latencies_ms"]
    assert any("Context retrieval failed" in warning for warning in result["warnings"])


def test_researcher_returns_ranked_evidence_pack(monkeypatch) -> None:
    def fake_search_context(*args, **kwargs):
        return [
            {
                "id": "auth-0",
                "document": "Auth stack uses JWT and Google OAuth.",
                "metadata": {"source": "auth.md", "chunk_index": 0},
                "distance": 0.2,
                "score": 0.9,
            },
            {
                "id": "security-1",
                "document": "OAuth callback failures must show a safe error.",
                "metadata": {"source": "security.md", "chunk_index": 1},
                "distance": 0.5,
                "score": 0.75,
            },
        ]

    monkeypatch.setattr(researcher, "search_context", fake_search_context)

    result = ResearcherAgent().run("Add Google login")

    assert result["retrieval_status"] == "ok"
    assert result["documents"] == [
        "Auth stack uses JWT and Google OAuth.",
        "OAuth callback failures must show a safe error.",
    ]
    assert result["ids"] == ["auth-0", "security-1"]
    assert result["matches"][0]["metadata"]["source"] == "auth.md"
    assert result["retrieved_sources"][0]["source"] == "auth.md"
    assert result["retrieved_sources"][0]["excerpt"] == "Auth stack uses JWT and Google OAuth."
    assert result["retrieval_threshold"] == 0.6
    assert result["raw_match_count"] == 2
    assert result["confidence"] == 0.9
    assert "source=auth.md" in result["context_snippets"][0]


def test_researcher_marks_empty_results(monkeypatch) -> None:
    monkeypatch.setattr(researcher, "search_context", lambda *args, **kwargs: [])

    result = ResearcherAgent().run("Add Google login")

    assert result["retrieval_status"] == "empty"
    assert result["matches"] == []
    assert result["confidence"] == 0.0
    assert any("No relevant project context" in warning for warning in result["warnings"])


def test_researcher_filters_matches_below_threshold(monkeypatch) -> None:
    def fake_search_context(*args, **kwargs):
        return [
            {
                "id": "weak-0",
                "document": "Unrelated text",
                "metadata": {"source": "misc.md", "chunk_index": 0},
                "distance": 1.4,
                "score": 0.3,
            }
        ]

    monkeypatch.setattr(researcher, "search_context", fake_search_context)

    result = ResearcherAgent().run("Add Google login")

    assert result["retrieval_status"] == "no_relevant_context"
    assert result["documents"] == []
    assert result["matches"] == []
    assert result["retrieved_sources"] == []
    assert result["raw_match_count"] == 1
    assert any("threshold" in warning for warning in result["warnings"])


def test_researcher_keeps_expected_domain_match_when_hybrid_score_is_low(monkeypatch) -> None:
    def fake_search_context(*args, **kwargs):
        return [
            {
                "id": "auth-context-0",
                "document": "Auth Context uses JWT-based authentication for login, logout, token refresh, and OAuth callback endpoints.",
                "metadata": {"source": "auth_context.md", "chunk_index": 0},
                "distance": 0.32,
                "score": 0.39,
                "vector_score": 0.84,
                "rank_score": 0.39,
            },
            {
                "id": "notification-context-0",
                "document": "Notification Context sends Slack and email alerts.",
                "metadata": {"source": "notification_context.md", "chunk_index": 0},
                "distance": 0.2,
                "score": 0.72,
                "vector_score": 0.9,
                "rank_score": 0.72,
            },
        ]

    monkeypatch.setattr(researcher, "search_context", fake_search_context)

    result = ResearcherAgent().run("Improve login")

    assert result["retrieval_status"] == "ok"
    assert result["documents"][0] == "Auth Context uses JWT-based authentication for login, logout, token refresh, and OAuth callback endpoints."
    assert result["retrieved_sources"][0]["source"] == "auth_context.md"
    assert result["retrieved_sources"][0]["score"] == 0.84
    assert result["selected_context_sources"][0]["source"] == "auth_context.md"
    # Non-expected sources with score >= threshold are now retained
    assert result["retrieval_status"] == "ok"
    assert result["confidence"] >= 0.7


def test_researcher_keeps_only_top_context_matches(monkeypatch) -> None:
    def fake_search_context(*args, **kwargs):
        return [
            {
                "id": f"auth-{index}",
                "document": f"Auth evidence {index}",
                "metadata": {"source": "auth.md", "chunk_index": index},
                "distance": 0.1 + index * 0.1,
                "score": score,
            }
            for index, score in enumerate([0.7, 0.95, 0.8, 0.9], start=1)
        ]

    monkeypatch.setattr(researcher, "search_context", fake_search_context)

    result = ResearcherAgent().run("Add Google login", n_results=4)

    # Source-level dedup: all 4 chunks are from auth.md, so only the best one is kept
    assert len(result["documents"]) == 1
    assert result["documents"][0] == "Auth evidence 2"  # highest score 0.95
    assert result["retrieved_sources"][0]["score"] == 1.0
    assert result["raw_match_count"] == 4


def test_researcher_truncates_evidence_excerpt(monkeypatch) -> None:
    agent = ResearcherAgent()
    agent.settings = Settings(retrieval_excerpt_chars=12)

    source = agent._build_retrieved_sources(
        [
            {
                "id": "auth-0",
                "document": "Auth stack uses JWT and Google OAuth.",
                "metadata": {"source": "auth.md", "chunk_index": 0},
                "distance": 0.2,
                "score": 0.9,
            }
        ]
    )

    assert source[0]["excerpt"] == "Auth stack u..."


def test_researcher_no_relevant_context_populates_planning_brief(monkeypatch) -> None:
    """Edge case: all results below threshold must still produce a usable planning brief."""
    def fake_search_context(*args, **kwargs):
        return [
            {
                "id": "noise-0",
                "document": "Unrelated marketing copy about branding.",
                "metadata": {"source": "marketing.md", "chunk_index": 0},
                "distance": 1.5,
                "score": 0.2,
            },
            {
                "id": "noise-1",
                "document": "Company holiday schedule 2026.",
                "metadata": {"source": "hr_policy.md", "chunk_index": 0},
                "distance": 1.8,
                "score": 0.1,
            },
        ]

    monkeypatch.setattr(researcher, "search_context", fake_search_context)

    result = ResearcherAgent().run("Add biometric fingerprint login")

    assert result["retrieval_status"] == "no_relevant_context"
    assert result["documents"] == []
    assert result["confidence"] == 0.0
    assert result["planning_brief"] is not None
    assert result["planning_brief"]["retrieval_status"] == "no_relevant_context"
    assert any("threshold" in w for w in result["warnings"])


def test_researcher_source_level_dedup_improves_precision(monkeypatch) -> None:
    """Source-level dedup: when 3 chunks come from auth.md and 1 from checkout.md,
    only the best chunk per source is kept, so both sources appear in top results."""
    def fake_search_context(*args, **kwargs):
        return [
            {
                "id": "auth-0",
                "document": "Auth chunk 1: JWT login flow.",
                "metadata": {"source": "auth.md", "chunk_index": 0},
                "distance": 0.1,
                "score": 0.95,
            },
            {
                "id": "auth-1",
                "document": "Auth chunk 2: OAuth callback.",
                "metadata": {"source": "auth.md", "chunk_index": 1},
                "distance": 0.15,
                "score": 0.90,
            },
            {
                "id": "auth-2",
                "document": "Auth chunk 3: Token refresh.",
                "metadata": {"source": "auth.md", "chunk_index": 2},
                "distance": 0.2,
                "score": 0.85,
            },
            {
                "id": "checkout-0",
                "document": "Checkout: payment retry with idempotency key.",
                "metadata": {"source": "checkout.md", "chunk_index": 0},
                "distance": 0.3,
                "score": 0.80,
            },
        ]

    monkeypatch.setattr(researcher, "search_context", fake_search_context)

    result = ResearcherAgent().run("Login and checkout integration", n_results=3)

    # Without source-level dedup, all 3 slots would be auth.md chunks.
    # With dedup, only the best auth.md chunk is kept + checkout.md appears.
    sources = [s["source"] for s in result["retrieved_sources"]]
    assert "auth.md" in sources
    assert "checkout.md" in sources
    assert len(result["retrieved_sources"]) == 2


def test_researcher_empty_chromadb_returns_actionable_warnings(monkeypatch) -> None:
    """Edge case: brand-new project with no documents ingested."""
    monkeypatch.setattr(researcher, "search_context", lambda *args, **kwargs: [])

    result = ResearcherAgent().run("Build entire payment gateway from scratch")

    assert result["retrieval_status"] == "empty"
    assert result["confidence"] == 0.0
    assert result["raw_match_count"] == 0
    assert result["documents"] == []
    assert result["retrieved_sources"] == []
    assert result["context_snippets"] == []
    assert any("No relevant project context" in w for w in result["warnings"])
    # Planning brief should exist and be usable even with no context
    assert result["planning_brief"]["retrieval_status"] == "empty"
    assert result["planning_brief"]["confidence"] == 0.0


def test_researcher_exception_returns_graceful_failure(monkeypatch) -> None:
    """Edge case: ChromaDB crashes during query."""
    def exploding_search(*args, **kwargs):
        raise ConnectionError("ChromaDB connection refused on port 8001")

    monkeypatch.setattr(researcher, "search_context", exploding_search)

    result = ResearcherAgent().run("Any requirement")

    assert result["retrieval_status"] == "failed"
    assert result["confidence"] == 0.0
    assert result["documents"] == []
    assert any("Context retrieval failed" in w for w in result["warnings"])
    assert any("ChromaDB connection refused" in w for w in result["warnings"])

