from types import SimpleNamespace

from ai_scrum_master.core.generation_quality import evaluate_grounded_generation, generation_quality_gate_passed
from ai_scrum_master.retrieval import rag


def test_build_ollama_embeddings_uses_configured_embedding_model(monkeypatch) -> None:
    captured = {}

    class FakeOllamaEmbeddings:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    def fake_import_module(module_name: str):
        assert module_name == "langchain_ollama"
        return SimpleNamespace(OllamaEmbeddings=FakeOllamaEmbeddings)

    monkeypatch.setattr(rag, "import_module", fake_import_module)

    rag.build_ollama_embeddings()

    assert captured["model"] == "nomic-embed-text"
    assert captured["base_url"] == "http://localhost:11434"


def test_rag_generation_quality_requires_valid_chunk_citations() -> None:
    matches = [
        {
            "id": "auth_context-0-abc123",
            "document": "Google OAuth callback must exchange code server-side.",
            "metadata": {"source": "auth_context.md", "chunk_index": 0},
        }
    ]
    answer = {
        "status": "ANSWERED",
        "answer": "The callback exchanges code server-side.",
        "citations": ["auth_context-0-abc123"],
        "unsupported_claims": [],
    }

    metrics = evaluate_grounded_generation(answer, matches)
    passed, failures = generation_quality_gate_passed(metrics)

    assert metrics["grounded"] is True
    assert metrics["citation_precision"] == 1.0
    assert passed is True
    assert failures == []


def test_rag_generation_quality_flags_invalid_citations() -> None:
    metrics = evaluate_grounded_generation(
        {
            "status": "ANSWERED",
            "answer": "Unsupported answer.",
            "citations": ["missing-chunk"],
            "unsupported_claims": ["Unsupported answer."],
        },
        [
            {
                "id": "auth_context-0-abc123",
                "document": "Auth context.",
                "metadata": {"source": "auth_context.md", "chunk_index": 0},
            }
        ],
    )

    passed, failures = generation_quality_gate_passed(metrics)

    assert metrics["grounded"] is False
    assert "missing-chunk" in metrics["invalid_citations"]
    assert passed is False
    assert failures


def test_rag_normalizes_model_citation_prefixes_and_suffix_placeholders() -> None:
    matches = [
        {
            "id": "scrum_guide_2020-24-d338101bd611",
            "document": "Sprint Review inspects the outcome of the Sprint.",
            "metadata": {"source": "scrum_guide_2020.pdf", "chunk_index": 24},
        },
        {
            "id": "scrum_guide_2020-25-ee1b0a6eb568",
            "document": "The Scrum Team presents results to stakeholders.",
            "metadata": {"source": "scrum_guide_2020.pdf", "chunk_index": 25},
        },
    ]

    citations = rag.normalize_answer_citations(
        [
            "CITATION_ID: scrum_guide_2020-24-d338101bd611",
            "chunk_id-25-ee1b0a6eb568",
            "chunk_id",
        ],
        matches,
    )

    assert citations == [
        "scrum_guide_2020-24-d338101bd611",
        "scrum_guide_2020-25-ee1b0a6eb568",
    ]
