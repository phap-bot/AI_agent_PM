from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

from ai_scrum_master.core.config import BASE_DIR, get_settings
from ai_scrum_master.core.vector_store import add_documents

SUPPORTED_EXTENSIONS = {".md", ".txt"}
DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 200


def iter_source_files(raw_docs_dir: Path) -> Iterable[Path]:
    for path in raw_docs_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP) -> list[str]:
    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def build_chunk_id(path: Path, chunk_index: int, chunk: str) -> str:
    digest = hashlib.sha1(f"{path}:{chunk_index}:{chunk}".encode("utf-8")).hexdigest()[:12]
    return f"{path.stem}-{chunk_index}-{digest}"


def ingest_raw_docs(raw_docs_dir: Path | None = None, collection_name: str | None = None) -> dict:
    settings = get_settings()
    source_dir = raw_docs_dir or BASE_DIR / "data" / "raw_docs"
    target_collection = collection_name or settings.context_collection

    documents: list[str] = []
    ids: list[str] = []
    metadatas: list[dict] = []

    for path in iter_source_files(source_dir):
        text = path.read_text(encoding="utf-8")
        for index, chunk in enumerate(chunk_text(text)):
            documents.append(chunk)
            ids.append(build_chunk_id(path, index, chunk))
            metadatas.append(
                {
                    "source": str(path.relative_to(source_dir)),
                    "chunk_index": index,
                    "file_type": path.suffix.lower(),
                }
            )

    if documents:
        add_documents(
            documents=documents,
            ids=ids,
            metadatas=metadatas,
            collection_name=target_collection,
        )

    return {
        "collection": target_collection,
        "source_dir": str(source_dir),
        "files_indexed": len({metadata["source"] for metadata in metadatas}),
        "chunks_indexed": len(documents),
    }


if __name__ == "__main__":
    print(ingest_raw_docs())
