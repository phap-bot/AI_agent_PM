import hashlib
from pathlib import Path

from ai_scrum_master.ingestion.ingest import build_chunk_id, build_chunk_metadata, document_hash, read_source_text, chunk_text


def test_chunk_text_splits_with_overlap() -> None:
    text = "a" * 25
    chunks = chunk_text(text, chunk_size=10, overlap=2)

    assert chunks == ["a" * 10, "a" * 10, "a" * 9]


def test_chunk_text_prefers_paragraph_boundaries() -> None:
    text = "Paragraph one has auth context.\n\nParagraph two has callback details.\n\nParagraph three has QA checks."

    chunks = chunk_text(text, chunk_size=55, overlap=0)

    assert chunks == [
        "Paragraph one has auth context.",
        "Paragraph two has callback details.",
        "Paragraph three has QA checks.",
    ]


def test_chunk_text_falls_back_to_line_then_words() -> None:
    text = "Line one has auth context.\nLine two has callback details."

    chunks = chunk_text(text, chunk_size=32, overlap=0)

    assert chunks == ["Line one has auth context.", "Line two has callback details."]


def test_chunk_text_ignores_empty_text() -> None:
    assert chunk_text("   ") == []


def test_build_chunk_id_is_stable_for_source_and_index() -> None:
    first = build_chunk_id(path=Path("auth/login.md"), chunk_index=0, chunk="old")
    second = build_chunk_id(path=Path("auth/login.md"), chunk_index=0, chunk="new")

    assert first == second


def test_build_chunk_metadata_includes_provenance_and_hashes(tmp_path) -> None:
    source_dir = tmp_path / "raw_docs"
    source_dir.mkdir()
    path = source_dir / "auth.md"
    path.write_text("Auth uses JWT", encoding="utf-8")

    metadata = build_chunk_metadata(
        path=path,
        source_dir=source_dir,
        chunk_index=0,
        chunk="Auth uses JWT",
        document_sha1="doc-hash",
        ingested_at="2026-05-26T00:00:00+00:00",
    )

    assert metadata["source"] == "auth.md"
    assert metadata["file_name"] == "auth.md"
    assert metadata["chunk_index"] == 0
    assert metadata["file_type"] == ".md"
    assert metadata["chunk_sha1"]
    assert metadata["document_sha1"] == "doc-hash"
    assert metadata["ingested_at"] == "2026-05-26T00:00:00+00:00"
    assert metadata["chunk_strategy"] == "langchain_recursive_character"


def test_read_source_text_reads_utf8_text_file(tmp_path) -> None:
    path = tmp_path / "auth.md"
    path.write_text("Đăng nhập bằng Google", encoding="utf-8")

    assert read_source_text(path) == "Đăng nhập bằng Google"


def test_document_hash_uses_pdf_bytes(tmp_path) -> None:
    path = tmp_path / "guide.pdf"
    path.write_bytes(b"%PDF-1.4\xff\x00binary")

    assert document_hash(path, "extracted text") == hashlib.sha1(path.read_bytes()).hexdigest()
