from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from typing import Any, Iterable, Sequence

from ai_scrum_master.core.config import BASE_DIR, get_settings
from ai_scrum_master.retrieval.rag import LANGCHAIN_INSTALL_HINT, add_langchain_documents
from ai_scrum_master.retrieval.vector_store import clear_collection

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}
DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_CHUNK_SEPARATORS = ("\n\n", "\n", ". ", " ", "")
CHUNK_STRATEGY = "langchain_recursive_character"


class IngestionDependencyError(ImportError):
    pass


def iter_source_files(raw_docs_dir: Path) -> Iterable[Path]:
    for path in raw_docs_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
    separators: Sequence[str] = DEFAULT_CHUNK_SEPARATORS,
) -> list[str]:
    text = text.strip()
    if not text:
        return []

    normalized = normalize_document_text(text)
    splitter = build_text_splitter(chunk_size=chunk_size, chunk_overlap=overlap, separators=separators)
    if splitter is not None:
        return [chunk for chunk in splitter.split_text(normalized) if chunk.strip()]

    if not any(separator and separator in normalized for separator in separators):
        return split_by_character_window(normalized, chunk_size=chunk_size, overlap=overlap)
    chunks = split_text_recursively(normalized, chunk_size=chunk_size, separators=separators)
    return apply_chunk_overlap(chunks, chunk_size=chunk_size, overlap=overlap)


def build_text_splitter(
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    separators: Sequence[str] = DEFAULT_CHUNK_SEPARATORS,
) -> Any | None:
    try:
        RecursiveCharacterTextSplitter = _load_langchain_attr(
            "langchain_text_splitters",
            "RecursiveCharacterTextSplitter",
        )
    except IngestionDependencyError:
        return None

    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=list(separators),
    )


def _load_langchain_attr(module_name: str, attr_name: str) -> Any:
    try:
        module = import_module(module_name)
    except ImportError as exc:
        raise IngestionDependencyError(
            f"Missing LangChain ingestion dependency '{module_name}'. {LANGCHAIN_INSTALL_HINT}"
        ) from exc
    return getattr(module, attr_name)


def normalize_document_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_text_recursively(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    separators: Sequence[str] = DEFAULT_CHUNK_SEPARATORS,
) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    if not separators:
        return split_by_character_window(text, chunk_size=chunk_size, overlap=0)

    separator = separators[0]
    if separator == "":
        return split_by_character_window(text, chunk_size=chunk_size, overlap=0)

    parts = [part.strip() for part in text.split(separator) if part.strip()]
    if len(parts) <= 1:
        return split_text_recursively(text, chunk_size=chunk_size, separators=separators[1:])

    chunks: list[str] = []
    current = ""
    for part in parts:
        if len(part) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(split_text_recursively(part, chunk_size=chunk_size, separators=separators[1:]))
            continue

        candidate = part if not current else f"{current}{separator}{part}"
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            current = part

    if current:
        chunks.append(current.strip())
    return chunks


def split_by_character_window(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [chunk for chunk in chunks if chunk]


def apply_chunk_overlap(chunks: list[str], chunk_size: int, overlap: int) -> list[str]:
    if overlap <= 0 or len(chunks) <= 1:
        return chunks

    overlapped = [chunks[0]]
    for index, chunk in enumerate(chunks[1:], start=1):
        previous_tail = chunks[index - 1][-overlap:].strip()
        if previous_tail and len(previous_tail) + 2 + len(chunk) <= chunk_size:
            overlapped.append(f"{previous_tail}\n\n{chunk}".strip())
        else:
            overlapped.append(chunk)
    return overlapped


def build_chunk_id(path: Path, chunk_index: int, chunk: str = "") -> str:
    digest = hashlib.sha1(f"{path.as_posix()}:{chunk_index}".encode("utf-8")).hexdigest()[:12]
    return f"{path.stem}-{chunk_index}-{digest}"


def build_chunk_metadata(path: Path, source_dir: Path, chunk_index: int, chunk: str, document_sha1: str, ingested_at: str) -> dict:
    relative_path = path.relative_to(source_dir)
    return {
        "source": relative_path.as_posix(),
        "source_path": str(path),
        "file_name": path.name,
        "chunk_index": chunk_index,
        "file_type": path.suffix.lower(),
        "chunk_sha1": hashlib.sha1(chunk.encode("utf-8")).hexdigest(),
        "document_sha1": document_sha1,
        "ingested_at": ingested_at,
        "chunk_strategy": CHUNK_STRATEGY,
        "chunk_size": get_settings().rag_chunk_size,
        "chunk_overlap": get_settings().rag_chunk_overlap,
    }


def read_source_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return read_pdf_text(path)
    return path.read_text(encoding="utf-8")


def read_pdf_text(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n\n".join(page.strip() for page in pages if page.strip())


def document_hash(path: Path, text: str) -> str:
    if path.suffix.lower() == ".pdf":
        return hashlib.sha1(path.read_bytes()).hexdigest()
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def load_source_documents(source_dir: Path) -> list[Any]:
    documents: list[Any] = []
    TextLoader = _load_langchain_attr("langchain_community.document_loaders", "TextLoader")
    PyPDFLoader = _load_langchain_attr("langchain_community.document_loaders", "PyPDFLoader")

    for path in iter_source_files(source_dir):
        if path.suffix.lower() == ".pdf":
            loader = PyPDFLoader(str(path))
        else:
            loader = TextLoader(str(path), encoding="utf-8")
        documents.extend(loader.load())
    return documents


def split_loaded_documents(documents: list[Any]) -> list[Any]:
    settings = get_settings()
    splitter = build_text_splitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        separators=DEFAULT_CHUNK_SEPARATORS,
    )
    if splitter is None:
        raise IngestionDependencyError(LANGCHAIN_INSTALL_HINT)
    return splitter.split_documents(documents)


def prepare_langchain_chunks(chunks: list[Any], source_dir: Path, ingested_at: str) -> tuple[list[Any], list[str]]:
    source_indexes: dict[str, int] = {}
    ids: list[str] = []
    prepared_chunks = []

    for chunk in chunks:
        source_path = resolve_chunk_source_path(chunk, source_dir)
        source_key = source_path.as_posix()
        chunk_index = source_indexes.get(source_key, 0)
        source_indexes[source_key] = chunk_index + 1

        text = normalize_document_text(str(chunk.page_content))
        document_sha1 = document_hash(source_path, read_source_text(source_path))
        chunk_id = build_chunk_id(source_path.relative_to(source_dir), chunk_index, text)
        metadata = build_chunk_metadata(
            path=source_path,
            source_dir=source_dir,
            chunk_index=chunk_index,
            chunk=text,
            document_sha1=document_sha1,
            ingested_at=ingested_at,
        )
        if "page" in chunk.metadata:
            metadata["page"] = chunk.metadata["page"]
        metadata["chunk_id"] = chunk_id
        metadata["id"] = chunk_id
        chunk.page_content = text
        chunk.metadata = metadata
        ids.append(chunk_id)
        prepared_chunks.append(chunk)

    return prepared_chunks, ids


def resolve_chunk_source_path(chunk: Any, source_dir: Path) -> Path:
    raw_source = str((chunk.metadata or {}).get("source") or "")
    path = Path(raw_source)
    if not path.is_absolute():
        path = source_dir / path
    return path.resolve()


def ingest_raw_docs(raw_docs_dir: Path | None = None, collection_name: str | None = None) -> dict:
    settings = get_settings()
    source_dir = raw_docs_dir or BASE_DIR / "data" / "raw_docs"
    target_collection = collection_name or settings.context_collection

    ingested_at = datetime.now(UTC).isoformat()
    loaded_documents = load_source_documents(source_dir)
    chunks, ids = prepare_langchain_chunks(
        split_loaded_documents(loaded_documents),
        source_dir=source_dir.resolve(),
        ingested_at=ingested_at,
    )

    if chunks:
        clear_collection(target_collection)
        add_langchain_documents(
            documents=chunks,
            ids=ids,
            collection_name=target_collection,
        )

    return {
        "collection": target_collection,
        "source_dir": str(source_dir),
        "files_indexed": len({chunk.metadata["source"] for chunk in chunks}),
        "chunks_indexed": len(chunks),
        "chunk_strategy": CHUNK_STRATEGY,
        "embedding_model": settings.embedding_model,
        "vector_store": "langchain_chroma",
    }


if __name__ == "__main__":
    print(ingest_raw_docs())
