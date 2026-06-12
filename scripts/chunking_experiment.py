"""
Chunking Strategy Experiment (W8 — Phuc)
=========================================
Thử nghiệm 3 chiến lược chunking khác nhau và so sánh RAG metrics
để tìm ra cấu hình tốt nhất cho hệ thống.

Strategies:
  A) chunk_size=800,  overlap=100  (nhỏ, ít overlap)
  B) chunk_size=1200, overlap=200  (hiện tại - baseline)
  C) chunk_size=1600, overlap=300  (lớn, nhiều overlap)

Chạy:
    .\.venv\Scripts\Activate.ps1
    $env:PYTHONPATH = "src"
    python scripts/chunking_experiment.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, 'src')

from ai_scrum_master.core.config import BASE_DIR, get_settings
from ai_scrum_master.core.quality_gate import evaluate_retrieval_cases
from ai_scrum_master.evaluation.rag_quality_check import QUERY_CASES, K
from ai_scrum_master.ingestion.ingest import (
    chunk_text,
    iter_source_files,
)
from ai_scrum_master.retrieval.vector_store import get_collection

# ---------------------------------------------------------------------------
# Experiment configurations
# ---------------------------------------------------------------------------
STRATEGIES: list[dict[str, Any]] = [
    {"name": "small_chunk",    "chunk_size": 800,  "overlap": 100},
    {"name": "baseline",       "chunk_size": 1200, "overlap": 200},
    {"name": "large_chunk",    "chunk_size": 1600, "overlap": 300},
]

EXPERIMENT_COLLECTION_PREFIX = "chunking_experiment"
RAW_DOCS_DIR = BASE_DIR / "data" / "raw_docs"


def ingest_with_strategy(
    strategy: dict[str, Any],
    collection_name: str,
) -> dict[str, Any]:
    """Re-ingest all raw docs with the given chunk_size and overlap into a temp collection."""
    settings = get_settings()

    # Build embeddings
    from ai_scrum_master.retrieval.rag import build_ollama_embeddings
    embeddings = build_ollama_embeddings()

    collection = get_collection(collection_name)

    # Clear collection if it already exists
    existing = collection.count()
    if existing > 0:
        collection.delete(where={"source": {"$ne": ""}})

    total_chunks = 0
    files_indexed = 0

    for path in iter_source_files(RAW_DOCS_DIR):
        if path.suffix.lower() == ".pdf":
            continue  # Skip PDFs for chunking experiment (focus on .md/.txt)

        text = path.read_text(encoding="utf-8", errors="replace")
        chunks = chunk_text(
            text,
            chunk_size=strategy["chunk_size"],
            overlap=strategy["overlap"],
        )
        if not chunks:
            continue

        ids = [f"{path.stem}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": path.name, "chunk_index": i} for i in range(len(chunks))]

        # Embed and add
        vectors = embeddings.embed_documents(chunks)
        collection.add(
            ids=ids,
            documents=chunks,
            embeddings=vectors,
            metadatas=metadatas,
        )
        total_chunks += len(chunks)
        files_indexed += 1

    return {
        "files_indexed": files_indexed,
        "total_chunks": total_chunks,
        "collection": collection_name,
    }


def evaluate_strategy(collection_name: str) -> dict[str, Any]:
    """Run the 30 GT queries against a specific collection and return metrics."""
    from ai_scrum_master.retrieval.vector_store import search_context

    def retriever(query: str, top_k: int) -> list[dict[str, Any]]:
        return search_context(query=query, n_results=top_k, collection_name=collection_name)

    cases = [{"query": c["query"], "expected_sources": c["expected_sources"]} for c in QUERY_CASES]
    return evaluate_retrieval_cases(cases, k=K, retriever=retriever)


def run_experiment() -> dict[str, Any]:
    """Run all strategies and collect results."""
    results = []

    for strategy in STRATEGIES:
        name = strategy["name"]
        collection_name = f"{EXPERIMENT_COLLECTION_PREFIX}_{name}"

        print(f"\n{'='*70}")
        print(f"  Strategy: {name} (chunk_size={strategy['chunk_size']}, overlap={strategy['overlap']})")
        print(f"{'='*70}")

        # Ingest
        print(f"  ⏳ Ingesting documents...")
        started = time.perf_counter()
        ingest_info = ingest_with_strategy(strategy, collection_name)
        ingest_ms = round((time.perf_counter() - started) * 1000)
        print(f"  ✅ Ingested {ingest_info['files_indexed']} files → {ingest_info['total_chunks']} chunks ({ingest_ms}ms)")

        # Evaluate
        print(f"  ⏳ Evaluating 30 queries...")
        started = time.perf_counter()
        eval_result = evaluate_strategy(collection_name)
        eval_ms = round((time.perf_counter() - started) * 1000)
        agg = eval_result["aggregate"]

        print(f"  📊 Results ({eval_ms}ms):")
        print(f"     Hit Rate@{K}: {agg['hit_rate_at_k']:.4f}")
        print(f"     Recall@{K}:   {agg['recall_at_k']:.4f}")
        print(f"     Precision@{K}:{agg['precision_at_k']:.4f}")
        print(f"     MRR:          {agg['mrr']:.4f}")
        print(f"     NDCG@{K}:     {agg['ndcg_at_k']:.4f}")

        results.append({
            "strategy": name,
            "chunk_size": strategy["chunk_size"],
            "overlap": strategy["overlap"],
            "chunks": ingest_info["total_chunks"],
            "ingest_ms": ingest_ms,
            "eval_ms": eval_ms,
            "metrics": agg,
        })

    return {"strategies": results}


def print_comparison(report: dict[str, Any]) -> None:
    """Print a comparison table of all strategies."""
    print(f"\n{'='*90}")
    print("  CHUNKING STRATEGY COMPARISON")
    print(f"{'='*90}")
    print(f"  {'Strategy':<16} {'Chunks':<8} {'HR@3':<8} {'Recall':<8} {'Prec':<8} {'MRR':<8} {'NDCG':<8}")
    print(f"  {'-'*85}")

    best_score = 0
    best_name = ""

    for s in report["strategies"]:
        m = s["metrics"]
        composite = (m["hit_rate_at_k"] + m["recall_at_k"] + m["precision_at_k"] + m["mrr"] + m["ndcg_at_k"]) / 5
        if composite > best_score:
            best_score = composite
            best_name = s["strategy"]
        marker = " ⭐" if s["strategy"] == "baseline" else ""
        print(f"  {s['strategy']:<16} {s['chunks']:<8} {m['hit_rate_at_k']:<8.4f} {m['recall_at_k']:<8.4f} {m['precision_at_k']:<8.4f} {m['mrr']:<8.4f} {m['ndcg_at_k']:<8.4f}{marker}")

    print(f"\n  🏆 Best overall: {best_name} (composite={best_score:.4f})")
    print(f"{'='*90}\n")


def main() -> None:
    print("\n🔬 CHUNKING STRATEGY EXPERIMENT")
    print(f"   Corpus: {RAW_DOCS_DIR}")
    print(f"   Queries: {len(QUERY_CASES)} GT samples")
    print(f"   Top-K: {K}")

    report = run_experiment()
    print_comparison(report)

    # Save report
    report_path = Path("src/ai_scrum_master/evaluation/chunking_experiment_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  [Report saved] {report_path}")


if __name__ == "__main__":
    main()
