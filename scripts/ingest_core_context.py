"""
Targeted ingestion script — chỉ ingest các core context files.
Bỏ qua swe_bench_* để tránh batch quá lớn.

Chạy:
    .venv\\Scripts\\Activate.ps1
    $env:PYTHONPATH = "src"
    python scripts/ingest_core_context.py
"""
from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path

# Force UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add src to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ai_scrum_master.core.config import get_settings
from ai_scrum_master.core.logging import get_logger

logger = get_logger(__name__)


CORE_CONTEXT_FILES = [
    "auth_context.md",
    "checkout_context.md",
    "notification_context.md",
    "sprint_policy.md",
    "scrum_guide_2020.pdf",
    "acceptance_criteria.pdf",
    "user_stories.pdf",
]


def ingest_core_files() -> None:
    settings = get_settings()
    raw_docs_dir = ROOT / "src" / "ai_scrum_master" / "data" / "raw_docs"

    print(f"\n{'='*60}")
    print("  Core Context Ingestion")
    print(f"  Source: {raw_docs_dir}")
    print(f"  Collection: {settings.context_collection}")
    print(f"  Ollama: {settings.ollama_base_url} / {settings.embedding_model}")
    print(f"{'='*60}\n")

    # Collect target files
    target_files = []
    for filename in CORE_CONTEXT_FILES:
        path = raw_docs_dir / filename
        if path.exists():
            target_files.append(path)
            print(f"  [FOUND] {filename} ({path.stat().st_size // 1024} KB)")
        else:
            print(f"  [MISSING] {filename}")

    if not target_files:
        print("[ERROR] No target files found!")
        sys.exit(1)

    print(f"\n  Files to ingest: {len(target_files)}")
    print("  Processing each file individually to avoid batch limit...\n")

    # Import ingestion tools
    from ai_scrum_master.ingestion.ingest import (
        chunk_text,
        build_chunk_id,
        build_chunk_metadata,
        normalize_document_text,
        document_hash,
        read_source_text,
        split_loaded_documents,
    )
    from ai_scrum_master.retrieval.vector_store import (
        upsert_documents,
        canonical_collection_name,
        get_collection,
    )
    from ai_scrum_master.ingestion.pdf_processing import (
        extract_pdf_document,
        normalize_pdf_document,
        chunk_pdf_document,
    )
    from langchain_core.documents import Document
    from langchain_ollama import OllamaEmbeddings
    from langchain_chroma import Chroma

    collection_name = canonical_collection_name()

    # Build embeddings using OllamaEmbeddings (LangChain)
    print(f"  Building OllamaEmbeddings (model={settings.embedding_model})...")
    embeddings = OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_base_url,
    )

    # Test embed first
    print("  Testing embedding connection...")
    t0 = time.time()
    _ = embeddings.embed_query("test")
    print(f"  Embed test OK in {time.time()-t0:.2f}s\n")

    # Initialize Chroma vector store
    chroma_dir = str(Path(settings.chroma_persist_dir).resolve())
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=chroma_dir,
    )

    total_chunks = 0
    from datetime import datetime, UTC
    ingested_at = datetime.now(UTC).isoformat()

    from ai_scrum_master.ingestion.ingest import build_text_splitter, DEFAULT_CHUNK_SEPARATORS

    splitter = build_text_splitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        separators=DEFAULT_CHUNK_SEPARATORS,
    )

    for path in target_files:
        print(f"  Processing: {path.name}")
        t_file = time.time()

        try:
            # Load document
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
                docs = chunk_pdf_document(
                    normalized,
                    document_factory=Document,
                    text_splitter=splitter,
                    chunk_size=settings.rag_chunk_size,
                    chunk_overlap=settings.rag_chunk_overlap,
                )
            else:
                text = read_source_text(path)
                docs = [Document(page_content=text, metadata={"source": str(path)})]
                if splitter:
                    docs = splitter.split_documents(docs)

            if not docs:
                print(f"    [SKIP] No content extracted from {path.name}")
                continue

            # Build IDs and metadata
            doc_hash = document_hash(path, read_source_text(path) if path.suffix != ".pdf" else "")
            ids = []
            for i, doc in enumerate(docs):
                chunk_id = build_chunk_id(path.relative_to(raw_docs_dir), i)
                meta = build_chunk_metadata(
                    path=path,
                    source_dir=raw_docs_dir,
                    chunk_index=i,
                    chunk=doc.page_content,
                    document_sha1=doc_hash,
                    ingested_at=ingested_at,
                )
                doc.metadata.update(meta)
                ids.append(chunk_id)

            # Embed and upsert file by file (small batches)
            BATCH = 50
            for batch_start in range(0, len(docs), BATCH):
                batch_docs = docs[batch_start:batch_start + BATCH]
                batch_ids  = ids[batch_start:batch_start + BATCH]
                vectorstore.add_documents(documents=batch_docs, ids=batch_ids)
                print(f"    Batch {batch_start//BATCH + 1}: {len(batch_docs)} chunks embedded")

            total_chunks += len(docs)
            print(f"    Done: {len(docs)} chunks in {time.time()-t_file:.1f}s\n")

        except Exception as exc:
            print(f"    [ERROR] {path.name}: {exc}")
            continue

    print(f"{'='*60}")
    print(f"  Ingestion complete! Total chunks: {total_chunks}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    ingest_core_files()
