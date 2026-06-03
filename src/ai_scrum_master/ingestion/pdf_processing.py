from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExtractedPDFPage:
    page_number: int
    text: str
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExtractedPDFDocument:
    path: Path
    pages: list[ExtractedPDFPage]
    extractor: str
    warnings: list[str] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return "\n\n".join(page.text.strip() for page in self.pages if page.text.strip()).strip()


def extract_pdf_with_pypdf(path: Path) -> ExtractedPDFDocument:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages: list[ExtractedPDFPage] = []
    warnings: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # pragma: no cover - defensive for malformed PDFs
            text = ""
            warning = f"page {index}: pypdf extraction failed: {exc}"
            warnings.append(warning)
            pages.append(ExtractedPDFPage(page_number=index, text=text, warnings=[warning]))
            continue
        pages.append(ExtractedPDFPage(page_number=index, text=text))
    if not any(page.text.strip() for page in pages):
        warnings.append("No extractable text found in PDF.")
    return ExtractedPDFDocument(path=path, pages=pages, extractor="pypdf", warnings=warnings)


def extract_pdf_document(path: Path, extractor: str = "auto", fallback_on_error: bool = True) -> ExtractedPDFDocument:
    # Placeholder for an optional opendataloader-pdf-backed extractor after API/dependency review.
    # Current auto mode intentionally falls back to the stable pypdf baseline.
    try:
        return extract_pdf_with_pypdf(path)
    except Exception:
        if not fallback_on_error:
            raise
        return ExtractedPDFDocument(
            path=path,
            pages=[],
            extractor="pypdf",
            warnings=["PDF extraction failed before text could be read."],
        )


def normalize_pdf_document(document: ExtractedPDFDocument, remove_headers_footers: bool = True) -> ExtractedPDFDocument:
    pages = list(document.pages)
    if remove_headers_footers:
        pages = remove_repeated_headers_footers(pages)
    normalized_pages = [
        ExtractedPDFPage(
            page_number=page.page_number,
            text=normalize_pdf_page_text(page.text),
            warnings=page.warnings,
        )
        for page in pages
    ]
    return ExtractedPDFDocument(
        path=document.path,
        pages=normalized_pages,
        extractor=document.extractor,
        warnings=document.warnings,
    )


def normalize_pdf_page_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    paragraphs = re.split(r"\n\s*\n", text.strip())
    normalized = [_normalize_pdf_paragraph(paragraph) for paragraph in paragraphs]
    return "\n\n".join(paragraph for paragraph in normalized if paragraph).strip()


def _normalize_pdf_paragraph(paragraph: str) -> str:
    lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
    if not lines:
        return ""
    output = lines[0]
    for line in lines[1:]:
        if output.endswith("-") and line and line[0].islower():
            output = output[:-1] + line
        elif _should_join_pdf_line(output, line):
            output = f"{output} {line}"
        else:
            output = f"{output}\n{line}"
    return re.sub(r" {2,}", " ", output).strip()


def _should_join_pdf_line(previous: str, current: str) -> bool:
    if not previous or not current:
        return False
    if previous.endswith(('.', ':', ';', '?', '!', ')', ']', '”', '"')):
        return False
    if re.match(r"^([\-•*]|\d+[.)])\s+", current):
        return False
    if current[:1].isupper() and len(previous) < 80:
        return False
    return True


def remove_repeated_headers_footers(pages: list[ExtractedPDFPage], min_repetitions: int = 2) -> list[ExtractedPDFPage]:
    if len(pages) < min_repetitions:
        return pages

    candidates: dict[str, int] = {}
    for page in pages:
        lines = [line.strip() for line in page.text.splitlines() if line.strip()]
        edge_lines = lines[:1] + lines[-1:]
        for line in edge_lines:
            normalized = _normalize_repeated_edge_line(line)
            if normalized:
                candidates[normalized] = candidates.get(normalized, 0) + 1

    repeated = {line for line, count in candidates.items() if count >= min_repetitions}
    if not repeated:
        return pages

    cleaned_pages = []
    for page in pages:
        lines = page.text.splitlines()
        cleaned = [line for line in lines if _normalize_repeated_edge_line(line) not in repeated]
        cleaned_pages.append(ExtractedPDFPage(page_number=page.page_number, text="\n".join(cleaned), warnings=page.warnings))
    return cleaned_pages


def _normalize_repeated_edge_line(line: str) -> str:
    normalized = re.sub(r"\s+", " ", line.strip().lower())
    normalized = re.sub(r"\bpage\s+\d+\b", "page #", normalized)
    normalized = re.sub(r"^\d+$", "#", normalized)
    if len(normalized) < 4 and normalized != "#":
        return ""
    return normalized


def chunk_pdf_document(
    document: ExtractedPDFDocument,
    document_factory: Any,
    text_splitter: Any | None,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Any]:
    chunks: list[Any] = []
    current_parts: list[str] = []
    current_pages: list[int] = []

    def flush() -> None:
        if not current_parts:
            return
        text = "\n\n".join(current_parts).strip()
        if not text:
            current_parts.clear()
            current_pages.clear()
            return
        chunks.extend(_documents_for_pdf_text(
            text=text,
            pages=current_pages,
            document=document,
            document_factory=document_factory,
            text_splitter=text_splitter,
        ))
        current_parts.clear()
        current_pages.clear()

    for page in document.pages:
        page_text = page.text.strip()
        if not page_text:
            continue
        if sum(len(part) for part in current_parts) + len(page_text) + 2 <= chunk_size:
            current_parts.append(page_text)
            current_pages.append(page.page_number)
        else:
            flush()
            if len(page_text) <= chunk_size:
                current_parts.append(page_text)
                current_pages.append(page.page_number)
            else:
                chunks.extend(_documents_for_pdf_text(
                    text=page_text,
                    pages=[page.page_number],
                    document=document,
                    document_factory=document_factory,
                    text_splitter=text_splitter,
                ))
    flush()
    return chunks


def _documents_for_pdf_text(
    text: str,
    pages: list[int],
    document: ExtractedPDFDocument,
    document_factory: Any,
    text_splitter: Any | None,
) -> list[Any]:
    split_texts = [text]
    if text_splitter is not None and len(text) > getattr(text_splitter, "_chunk_size", len(text)):
        split_texts = [chunk for chunk in text_splitter.split_text(text) if chunk.strip()]
    page_start = min(pages) if pages else None
    page_end = max(pages) if pages else None
    metadata = {
        "source": str(document.path),
        "extractor": document.extractor,
        "page_start": page_start,
        "page_end": page_end,
        "page_numbers": ",".join(str(page) for page in sorted(set(pages))),
        "extraction_warnings": "; ".join(document.warnings),
        "text_quality_flags": "empty_pdf_text" if not document.full_text else "",
        "chunk_strategy": "pdf_page_semantic_recursive_character",
    }
    return [document_factory(page_content=chunk.strip(), metadata=dict(metadata)) for chunk in split_texts if chunk.strip()]
