from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ai_scrum_master.core.config import get_settings
from ai_scrum_master.core.generation_quality import (
    evaluate_grounded_generation,
    generation_quality_gate_passed,
)
from ai_scrum_master.core.quality_gate import (
    evaluate_retrieved_matches,
    expected_relevance_for_case,
    quality_gate_passed,
)
from ai_scrum_master.retrieval.rag import generate_answer_from_matches
from ai_scrum_master.retrieval.vector_store import search_context


def load_cases(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate LangChain RAG retrieval and grounded generation quality.")
    parser.add_argument("--queries", default="data/test_queries.json", help="Path to RAG evaluation query JSON.")
    parser.add_argument("--k", type=int, default=3, help="Top-k retrieved chunks.")
    parser.add_argument("--collection", default=None, help="Optional Chroma collection name.")
    parser.add_argument("--skip-generation", action="store_true", help="Only evaluate retrieval metrics.")
    args = parser.parse_args()

    settings = get_settings()
    collection_name = args.collection or settings.context_collection
    cases = load_cases(Path(args.queries))
    query_reports = []
    retrieval_totals = {
        "hit_rate_at_k": 0.0,
        "recall_at_k": 0.0,
        "precision_at_k": 0.0,
        "mrr": 0.0,
        "ndcg_at_k": 0.0,
    }
    generation_totals = {
        "grounded": 0.0,
        "answer_has_citation": 0.0,
        "citation_precision": 0.0,
        "unsupported_claim_count": 0.0,
    }

    for case in cases:
        query = case["query"]
        matches = search_context(query=query, n_results=args.k, collection_name=collection_name)
        retrieval_metrics = evaluate_retrieved_matches(
            matches,
            expected_relevance_for_case(case),
            k=args.k,
        )
        for metric in retrieval_totals:
            retrieval_totals[metric] += float(retrieval_metrics[metric])

        report = {
            "query": query,
            "retrieval": retrieval_metrics,
        }
        if not args.skip_generation:
            answer = generate_answer_from_matches(query, matches)
            generation_metrics = evaluate_grounded_generation(answer, matches)
            for metric in generation_totals:
                generation_totals[metric] += float(generation_metrics[metric])
            report["generation"] = {
                "answer": answer.get("answer", ""),
                "citations": answer.get("citations", []),
                "metrics": generation_metrics,
            }
        query_reports.append(report)

    total = len(query_reports) or 1
    retrieval_aggregate = {key: round(value / total, 4) for key, value in retrieval_totals.items()}
    retrieval_passed, retrieval_failures = quality_gate_passed(retrieval_aggregate)
    report = {
        "backend": settings.rag_backend,
        "embedding_model": settings.embedding_model,
        "generation_model": settings.reasoning_model,
        "collection": collection_name,
        "top_k": args.k,
        "retrieval": {
            "aggregate": retrieval_aggregate,
            "quality_gate": {
                "passed": retrieval_passed,
                "failures": retrieval_failures,
            },
        },
        "queries": query_reports,
    }

    exit_code = 0 if retrieval_passed else 1
    if not args.skip_generation:
        generation_aggregate = {key: round(value / total, 4) for key, value in generation_totals.items()}
        generation_passed, generation_failures = generation_quality_gate_passed(
            {
                "answer_has_citation": generation_aggregate["answer_has_citation"] == 1.0,
                "citation_precision": generation_aggregate["citation_precision"],
                "unsupported_claim_count": generation_aggregate["unsupported_claim_count"],
                "invalid_citations": [],
            }
        )
        report["generation"] = {
            "aggregate": generation_aggregate,
            "quality_gate": {
                "passed": generation_passed,
                "failures": generation_failures,
            },
        }
        exit_code = 0 if retrieval_passed and generation_passed else 1

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
