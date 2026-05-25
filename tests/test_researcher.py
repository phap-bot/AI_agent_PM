from ai_scrum_master.agents import researcher
from ai_scrum_master.agents.researcher import ResearcherAgent


def test_researcher_returns_empty_context_when_query_fails(monkeypatch) -> None:
    def broken_query_documents(*args, **kwargs):
        raise RuntimeError("chroma unavailable")

    monkeypatch.setattr(researcher, "query_documents", broken_query_documents)

    result = ResearcherAgent().run("Add Google login")

    assert result["documents"] == []
    assert result["confidence"] == 0.0
    assert any("Context retrieval failed" in warning for warning in result["warnings"])
