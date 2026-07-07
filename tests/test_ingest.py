import hashlib
from pathlib import Path

from ai_scrum_master.ingestion.ingest import (
    _compute_file_hash,
    build_chunk_id,
    build_chunk_metadata,
    chunk_text,
    document_hash,
    read_source_text,
    resolve_chunk_source_path,
)
from ai_scrum_master.ingestion.pdf_processing import (
    ExtractedPDFDocument,
    ExtractedPDFPage,
    chunk_pdf_document,
    normalize_pdf_document,
    normalize_pdf_page_text,
    remove_repeated_headers_footers,
)


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


def test_build_chunk_id_is_scoped_by_project() -> None:
    first = build_chunk_id(path=Path("auth/login.md"), chunk_index=0, project_id="project-a")
    second = build_chunk_id(path=Path("auth/login.md"), chunk_index=0, project_id="project-b")

    assert first != second


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


def test_build_chunk_metadata_includes_project_id_when_present(tmp_path) -> None:
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
        project_id="project-123",
    )

    assert metadata["project_id"] == "project-123"


def test_read_source_text_reads_utf8_text_file(tmp_path) -> None:
    path = tmp_path / "auth.md"
    path.write_text("Đăng nhập bằng Google", encoding="utf-8")

    assert read_source_text(path).strip() == "Đăng nhập bằng Google"


def test_document_hash_uses_pdf_bytes(tmp_path) -> None:
    path = tmp_path / "guide.pdf"
    path.write_bytes(b"%PDF-1.4\xff\x00binary")

    assert document_hash(path, "extracted text") == hashlib.sha1(path.read_bytes()).hexdigest()


def test_compute_file_hash_uses_docx_bytes(tmp_path) -> None:
    path = tmp_path / "guide.docx"
    path.write_bytes(b"PK\x03\x04docx-binary")

    assert _compute_file_hash(path) == hashlib.sha1(path.read_bytes()).hexdigest()


def test_resolve_chunk_source_path_accepts_project_relative_loader_source(tmp_path, monkeypatch) -> None:
    source_dir = tmp_path / "project" / "raw_docs"
    source_dir.mkdir(parents=True)
    path = source_dir / "auth.md"
    path.write_text("Auth uses JWT", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    class Chunk:
        metadata = {"source": "project/raw_docs/auth.md"}

    resolved = resolve_chunk_source_path(Chunk(), source_dir.resolve())

    assert resolved == path.resolve()


def test_normalize_pdf_page_text_repairs_line_wrap_and_hyphenation() -> None:
    text = "This para-\ngraph keeps flowing\nwith context.\n\n- Keep this list item\nNext Section"

    normalized = normalize_pdf_page_text(text)

    assert "This paragraph keeps flowing with context." in normalized
    assert "- Keep this list item\nNext Section" in normalized


def test_remove_repeated_headers_footers_removes_page_edges() -> None:
    pages = [
        ExtractedPDFPage(1, "Project Guide\nAlpha context\nPage 1"),
        ExtractedPDFPage(2, "Project Guide\nBeta context\nPage 2"),
    ]

    cleaned = remove_repeated_headers_footers(pages)

    assert cleaned[0].text == "Alpha context"
    assert cleaned[1].text == "Beta context"


def test_normalize_pdf_document_preserves_page_numbers() -> None:
    document = ExtractedPDFDocument(
        path=Path("guide.pdf"),
        pages=[ExtractedPDFPage(3, "Wrapped\ncontext")],
        extractor="pypdf",
    )

    normalized = normalize_pdf_document(document)

    assert normalized.pages[0].page_number == 3
    assert normalized.pages[0].text == "Wrapped context"


def test_chunk_pdf_document_adds_page_metadata() -> None:
    class Document:
        def __init__(self, page_content, metadata):
            self.page_content = page_content
            self.metadata = metadata

    document = ExtractedPDFDocument(
        path=Path("guide.pdf"),
        pages=[
            ExtractedPDFPage(1, "Alpha context."),
            ExtractedPDFPage(2, "Beta context."),
        ],
        extractor="pypdf",
        warnings=["low confidence"],
    )

    chunks = chunk_pdf_document(
        document,
        document_factory=Document,
        text_splitter=None,
        chunk_size=100,
        chunk_overlap=0,
    )

    assert len(chunks) == 1
    assert chunks[0].metadata["source"] == "guide.pdf"
    assert chunks[0].metadata["extractor"] == "pypdf"
    assert chunks[0].metadata["page_start"] == 1
    assert chunks[0].metadata["page_end"] == 2
    assert chunks[0].metadata["page_numbers"] == "1,2"
    assert chunks[0].metadata["extraction_warnings"] == "low confidence"
    assert chunks[0].metadata["chunk_strategy"] == "pdf_page_semantic_recursive_character"
