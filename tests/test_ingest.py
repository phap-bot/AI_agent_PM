from ai_scrum_master.ingestion.ingest import chunk_text


def test_chunk_text_splits_with_overlap() -> None:
    text = "a" * 25
    chunks = chunk_text(text, chunk_size=10, overlap=2)

    assert chunks == ["a" * 10, "a" * 10, "a" * 9]


def test_chunk_text_ignores_empty_text() -> None:
    assert chunk_text("   ") == []
