from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ai_scrum_master.core.config import get_settings
from ai_scrum_master.core.quality_gate import evaluate_retrieval_cases, quality_gate_passed
from ai_scrum_master.retrieval.vector_store import search_context


def load_cases(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate retrieval baseline quality for the configured Chroma collection.")
    parser.add_argument("--queries", default="data/test_queries.json", help="Path to retrieval baseline query JSON.")
    parser.add_argument("--k", type=int, default=3, help="Top-k retrieved chunks to evaluate.")
    parser.add_argument("--collection", default=None, help="Optional Chroma collection name.")
    parser.add_argument("--min-hit-rate", type=float, default=0.8)
    parser.add_argument("--min-recall", type=float, default=0.7)
    parser.add_argument("--min-precision", type=float, default=0.5)
    parser.add_argument("--min-mrr", type=float, default=0.7)
    parser.add_argument("--min-ndcg", type=float, default=0.7)
    args = parser.parse_args()

    settings = get_settings()
    collection_name = args.collection or settings.context_collection
    cases = load_cases(Path(args.queries))

    report = evaluate_retrieval_cases(
        cases,
        k=args.k,
        retriever=lambda query, top_k: search_context(query=query, n_results=top_k, collection_name=collection_name),
    )
    passed, failures = quality_gate_passed(
        report["aggregate"],
        min_hit_rate=args.min_hit_rate,
        min_recall=args.min_recall,
        min_precision=args.min_precision,
        min_mrr=args.min_mrr,
        min_ndcg=args.min_ndcg,
    )
    report["quality_gate"] = {"passed": passed, "failures": failures}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
