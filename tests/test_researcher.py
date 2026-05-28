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
    assert result["documents"] == [
        "Auth Context uses JWT-based authentication for login, logout, token refresh, and OAuth callback endpoints."
    ]
    assert result["retrieved_sources"][0]["source"] == "auth_context.md"
    assert result["retrieved_sources"][0]["score"] == 0.84
    assert result["selected_context_sources"][0]["source"] == "auth_context.md"
    assert result["ignored_context_sources"] == []
    assert result["quality_gate"]["passed"] is True


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

    assert result["documents"] == ["Auth evidence 2", "Auth evidence 4", "Auth evidence 3"]
    assert [source["score"] for source in result["retrieved_sources"]] == [0.95, 0.9, 0.8]
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
