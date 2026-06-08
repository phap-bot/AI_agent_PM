from __future__ import annotations

import hashlib
import re
import time
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from typing import Any, Iterable, Sequence

from ai_scrum_master.core.config import BASE_DIR, get_settings
from ai_scrum_master.core.logging import get_logger
from ai_scrum_master.ingestion.pdf_processing import (
    chunk_pdf_document,
    extract_pdf_document,
    normalize_pdf_document,
)
from ai_scrum_master.retrieval.rag import LANGCHAIN_INSTALL_HINT, add_langchain_documents
from ai_scrum_master.retrieval.vector_store import canonical_collection_name

logger = get_logger(__name__)

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


def build_chunk_metadata(path: Path, source_dir: Path, chunk_index: int, chunk: str, document_sha1: str, ingested_at: str, project_id: str | None = None) -> dict:
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
        "project_id": project_id or "",
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
    Document = _load_langchain_attr("langchain_core.documents", "Document")
    settings = get_settings()
    splitter = build_text_splitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        separators=DEFAULT_CHUNK_SEPARATORS,
    )

    for path in iter_source_files(source_dir):
        if path.suffix.lower() == ".pdf" and settings.pdf_semantic_chunking:
            extracted = extract_pdf_document(
                path,
                extractor=settings.pdf_extractor,
                fallback_on_error=settings.pdf_fallback_on_error,
            )
            normalized = normalize_pdf_document(
                extracted,
                remove_headers_footers=settings.pdf_remove_headers_footers,
            )
            documents.extend(
                chunk_pdf_document(
                    normalized,
                    document_factory=Document,
                    text_splitter=splitter,
                    chunk_size=settings.rag_chunk_size,
                    chunk_overlap=settings.rag_chunk_overlap,
                )
            )
            continue

        text = read_source_text(path)
        if text.strip():
            documents.append(Document(page_content=text, metadata={"source": str(path)}))
    return documents


def load_source_documents_from_paths(paths: list[Path], source_dir: Path) -> list[Any]:
    """Load documents from specific file paths only (used by incremental ingestion)."""
    documents: list[Any] = []
    Document = _load_langchain_attr("langchain_core.documents", "Document")
    settings = get_settings()
    splitter = build_text_splitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        separators=DEFAULT_CHUNK_SEPARATORS,
    )

    for path in paths:
        logger.info("[INGEST] Loading file: %s", path.name)
        if path.suffix.lower() == ".pdf" and settings.pdf_semantic_chunking:
            extracted = extract_pdf_document(
                path,
                extractor=settings.pdf_extractor,
                fallback_on_error=settings.pdf_fallback_on_error,
            )
            normalized = normalize_pdf_document(
                extracted,
                remove_headers_footers=settings.pdf_remove_headers_footers,
            )
            documents.extend(
                chunk_pdf_document(
                    normalized,
                    document_factory=Document,
                    text_splitter=splitter,
                    chunk_size=settings.rag_chunk_size,
                    chunk_overlap=settings.rag_chunk_overlap,
                )
            )
            continue

        text = read_source_text(path)
        if text.strip():
            documents.append(Document(page_content=text, metadata={"source": str(path)}))
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


def prepare_langchain_chunks(chunks: list[Any], source_dir: Path, ingested_at: str, project_id: str | None = None) -> tuple[list[Any], list[str]]:
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
            project_id=project_id,
        )
        for key in (
            "page",
            "page_start",
            "page_end",
            "page_numbers",
            "extractor",
            "section_title",
            "block_types",
            "extraction_warnings",
            "text_quality_flags",
        ):
            if key in chunk.metadata and chunk.metadata[key] not in (None, ""):
                metadata[key] = chunk.metadata[key]
        metadata["chunk_strategy"] = chunk.metadata.get("chunk_strategy", metadata["chunk_strategy"])
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
        cwd_relative = path.resolve()
        if cwd_relative.exists():
            return cwd_relative
        path = source_dir / path
    return path.resolve()


def _get_existing_doc_hashes(collection_name: str) -> set[str]:
    """Query Qdrant for all unique document_sha1 values already ingested."""
    try:
        from ai_scrum_master.retrieval.vector_store import get_qdrant_client, canonical_collection_name
        client = get_qdrant_client()
        collection = canonical_collection_name(collection_name)
        
        if not client.collection_exists(collection_name=collection):
            return set()
            
        hashes = set()
        offset = None
        while True:
            records, next_offset = client.scroll(
                collection_name=collection,
                limit=1000,
                with_payload=["document_sha1"],
                with_vectors=False,
                offset=offset,
            )
            for record in records:
                if record.payload and record.payload.get("document_sha1"):
                    hashes.add(record.payload["document_sha1"])
                    
            if next_offset is None:
                break
            offset = next_offset
            
        logger.info("[INGEST] Found %d unique document hashes already in collection '%s'", len(hashes), collection)
        return hashes
    except Exception as exc:
        logger.warning("[INGEST] Could not query existing hashes, will re-index all: %s", exc)
        return set()


def _compute_file_hash(path: Path) -> str:
    """Compute document hash from raw file bytes (fast, no parsing needed)."""
    if path.suffix.lower() == ".pdf":
        return hashlib.sha1(path.read_bytes()).hexdigest()
    return hashlib.sha1(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def ingest_raw_docs(raw_docs_dir: Path | None = None, collection_name: str | None = None, project_id: str | None = None) -> dict:
    settings = get_settings()
    source_dir = raw_docs_dir or BASE_DIR / "data" / "raw_docs"
    
    # If project_id is provided and we are using the default directory, append project_id
    if not raw_docs_dir and project_id:
        source_dir = source_dir / project_id
        
    target_collection = canonical_collection_name(collection_name)
    t_start = time.time()

    logger.info("[INGEST] === Starting ingestion ===")
    logger.info("[INGEST] source_dir=%s  collection=%s project_id=%s", source_dir, target_collection, project_id)

    # --- Step 1: Get existing hashes for incremental ingestion ---
    existing_hashes = _get_existing_doc_hashes(target_collection)

    # --- Step 2: Filter files BEFORE loading (fast hash check on raw bytes) ---
    all_source_files = list(iter_source_files(source_dir))
    logger.info("[INGEST] Found %d source files in directory", len(all_source_files))

    new_files: list[Path] = []
    skipped_count = 0
    skipped_files: list[str] = []
    for path in all_source_files:
        try:
            file_hash = _compute_file_hash(path)
        except Exception as exc:
            logger.warning("[INGEST] Could not hash %s, treating as new: %s", path.name, exc)
            new_files.append(path)
            continue

        if file_hash in existing_hashes:
            logger.info("[INGEST] SKIP (unchanged) file=%s hash=%s", path.name, file_hash[:12])
            skipped_count += 1
            skipped_files.append(path.name)
        else:
            logger.info("[INGEST] NEW/CHANGED file=%s hash=%s", path.name, file_hash[:12])
            new_files.append(path)

    logger.info("[INGEST] Incremental filter: %d new files, %d skipped (already indexed)", len(new_files), skipped_count)

    ingested_at = datetime.now(UTC).isoformat()
    chunks_indexed = 0
    files_indexed = 0
    indexed_files: list[str] = []

    if new_files:
        # --- Step 3: Load ONLY new files ---
        t_load = time.time()
        new_documents = load_source_documents_from_paths(new_files, source_dir)
        logger.info("[INGEST] Loaded %d documents from %d new files in %.2fs",
                     len(new_documents), len(new_files), time.time() - t_load)

        # --- Step 4: Chunk new documents ---
        t_chunk = time.time()
        chunks, ids = prepare_langchain_chunks(
            split_loaded_documents(new_documents),
            source_dir=source_dir.resolve(),
            ingested_at=ingested_at,
            project_id=project_id,
        )
        logger.info("[INGEST] Chunked into %d pieces in %.2fs", len(chunks), time.time() - t_chunk)

        # --- Step 5: Upsert (NOT clear+add) for incremental ---
        if chunks:
            t_embed = time.time()
            add_langchain_documents(
                documents=chunks,
                ids=ids,
                collection_name=target_collection,
            )
            logger.info("[INGEST] Embedded & upserted %d chunks in %.2fs", len(chunks), time.time() - t_embed)
            files_indexed = len({chunk.metadata["source"] for chunk in chunks})
            chunks_indexed = len(chunks)
            indexed_files = [f.name for f in new_files]
    else:
        logger.info("[INGEST] No new files to index, skipping load/embed entirely.")

    total_time = time.time() - t_start
    logger.info("[INGEST] === Done in %.2fs === files_indexed=%d chunks_indexed=%d skipped=%d",
                total_time, files_indexed, chunks_indexed, skipped_count)

    return {
        "collection": target_collection,
        "source_dir": str(source_dir),
        "files_indexed": files_indexed,
        "chunks_indexed": chunks_indexed,
        "skipped_count": skipped_count,
        "indexed_files": indexed_files,
        "skipped_files": skipped_files,
        "chunk_strategy": CHUNK_STRATEGY,
        "embedding_model": settings.embedding_model,
        "vector_store": "langchain_qdrant",
    }


if __name__ == "__main__":
    print(ingest_raw_docs())
