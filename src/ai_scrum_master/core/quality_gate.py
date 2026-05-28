from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Callable

from ai_scrum_master.core.domain_profiles import DOMAIN_PROFILES
from ai_scrum_master.core.quality import OVERSIZED_REQUEST, classify_requirement
from ai_scrum_master.core.requirement_router import route_requirement
from ai_scrum_master.retrieval.vector_store import search_context

GUIDANCE_EXPECTED_SOURCES = {
    "acceptance criteria": {"acceptance_criteria": 1.0},
    "user story": {"user_stories": 1.0},
    "user stories": {"user_stories": 1.0},
    "epic": {"user_stories": 1.0},
    "invest": {"user_stories": 1.0},
    "definition of done": {"scrum_guide_2020": 0.8, "acceptance_criteria": 0.6},
}


def normalize_source_name(source: str) -> str:
    normalized = source.replace("\\", "/").split("/")[-1].lower()
    for suffix in (".md", ".txt", ".pdf"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
    return normalized


def relevance_for_match(match: dict[str, Any], expected_relevance: dict[str, float]) -> float:
    source = _match_source(match)
    return float(expected_relevance.get(source, 0.0))


def expected_relevance_for_case(case: dict[str, Any]) -> dict[str, float]:
    relevance = case.get("expected_relevance") or case.get("source_relevance")
    if isinstance(relevance, dict) and relevance:
        return {normalize_source_name(str(source)): float(score) for source, score in relevance.items()}
    return {normalize_source_name(str(source)): 1.0 for source in case.get("expected_sources", [])}


def expected_relevance_for_requirement(requirement: str, route: dict[str, Any] | None = None) -> dict[str, float]:
    route = route or route_requirement(requirement)
    if route:
        profile = route.get("profile", route)
        relevance = {normalize_source_name(str(source)): 1.0 for source in profile.get("required_sources", [])}
        relevance.update({normalize_source_name(str(source)): 0.5 for source in profile.get("optional_sources", [])})
        if relevance:
            return relevance
    text = requirement.lower()
    for phrase, sources in GUIDANCE_EXPECTED_SOURCES.items():
        if phrase in text:
            return sources
    if classify_requirement(requirement) == OVERSIZED_REQUEST:
        profile = DOMAIN_PROFILES["oversized_request"]
        return {
            normalize_source_name(str(source)): 0.5
            for source in profile.get("optional_sources", [])
        }
    return {}


def evaluate_research_output(
    requirement: str,
    matches: list[dict[str, Any]],
    k: int = 3,
    min_hit_rate: float = 1.0,
    min_recall: float = 1.0,
    min_precision: float = 0.33,
    min_mrr: float = 1.0,
    min_ndcg: float = 0.7,
    route: dict[str, Any] | None = None,
) -> dict[str, Any]:
    route_profile = (route or {}).get("profile", route or {})
    required_sources = {normalize_source_name(str(source)) for source in route_profile.get("required_sources", [])}
    optional_sources = {normalize_source_name(str(source)) for source in route_profile.get("optional_sources", [])}
    expected_relevance = expected_relevance_for_requirement(requirement, route)
    if not expected_relevance:
        return {
            "agent": "researcher",
            "passed": bool(matches),
            "expected_sources": [],
            "metrics": {
                "top_k": k,
                "retrieved_count": len(matches[:k]),
                "hit_rate_at_k": 1.0 if matches else 0.0,
                "recall_at_k": 1.0 if matches else 0.0,
                "precision_at_k": 1.0 if matches else 0.0,
                "mrr": 1.0 if matches else 0.0,
                "ndcg_at_k": 1.0 if matches else 0.0,
            },
            "failures": [] if matches else ["No context retrieved for requirement."],
        }

    metrics = evaluate_retrieved_matches(matches, expected_relevance, k=k)
    thresholds = {
        "hit_rate_at_k": min_hit_rate,
        "recall_at_k": min_recall,
        "precision_at_k": min_precision,
        "mrr": min_mrr,
        "ndcg_at_k": min_ndcg,
    }
    found_sources = set(metrics.get("found_sources", []))
    missing_required = sorted(source for source in required_sources if source not in found_sources)
    wrong_domain_sources = [
        source
        for source in metrics.get("retrieved_sources", [])
        if source and source not in required_sources and source not in optional_sources and bool(required_sources or optional_sources)
    ]
    metric_failures = [
        f"{metric}={metrics.get(metric, 0.0):.4f} below threshold {threshold:.4f}"
        for metric, threshold in thresholds.items()
        if metrics.get(metric, 0.0) < threshold
    ]
    hard_failures = []
    if required_sources and missing_required:
        hard_failures.append(f"Missing required source(s): {', '.join(missing_required)}")
    if required_sources and not found_sources:
        hard_failures.append("No usable required evidence was retrieved.")
    if wrong_domain_sources and not found_sources:
        hard_failures.append(f"Retrieved context is wrong domain: {', '.join(sorted(set(wrong_domain_sources)))}")
    if not route:
        hard_failures = metric_failures
    return {
        "agent": "researcher",
        "passed": not hard_failures,
        "expected_sources": sorted(expected_relevance),
        "required_sources": sorted(required_sources),
        "optional_sources": sorted(optional_sources),
        "metrics": metrics,
        "failures": hard_failures,
        "metric_warnings": [] if hard_failures else metric_failures,
    }


def dcg(relevance_scores: list[float]) -> float:
    return sum((2**score - 1) / math.log2(index + 2) for index, score in enumerate(relevance_scores))


def evaluate_retrieved_matches(matches: list[dict[str, Any]], expected_relevance: dict[str, float], k: int = 3) -> dict[str, Any]:
    top_matches = matches[:k]
    relevance_scores = [relevance_for_match(match, expected_relevance) for match in top_matches]
    relevant_flags = [score > 0 for score in relevance_scores]
    expected_sources = set(expected_relevance)
    seen_ndcg_sources: set[str] = set()
    ndcg_relevance_scores = []
    for match in top_matches:
        source = _match_source(match)
        if source in seen_ndcg_sources:
            ndcg_relevance_scores.append(0.0)
            continue
        seen_ndcg_sources.add(source)
        ndcg_relevance_scores.append(float(expected_relevance.get(source, 0.0)))
    found_sources = {
        _match_source(match)
        for match, relevant in zip(top_matches, relevant_flags, strict=False)
        if relevant
    }

    first_relevant_rank = next((index + 1 for index, relevant in enumerate(relevant_flags) if relevant), None)
    ideal_scores = sorted(expected_relevance.values(), reverse=True)[:k]
    ideal_dcg = dcg(ideal_scores)
    ndcg = dcg(ndcg_relevance_scores) / ideal_dcg if ideal_dcg else 0.0

    return {
        "top_k": k,
        "retrieved_count": len(top_matches),
        "retrieved_sources": [_match_source(match) for match in top_matches],
        "expected_sources": sorted(expected_sources),
        "found_sources": sorted(found_sources),
        "hit_rate_at_k": 1.0 if any(relevant_flags) else 0.0,
        "recall_at_k": len(found_sources) / len(expected_sources) if expected_sources else 0.0,
        "precision_at_k": sum(1 for flag in relevant_flags if flag) / k if k else 0.0,
        "mrr": 1.0 / first_relevant_rank if first_relevant_rank else 0.0,
        "ndcg_at_k": round(ndcg, 4),
        "relevance_scores": relevance_scores,
        "ndcg_relevance_scores": ndcg_relevance_scores,
    }


def evaluate_retrieval_cases(
    cases: list[dict[str, Any]],
    k: int = 3,
    retriever: Callable[[str, int], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    retriever = retriever or (lambda query, top_k: search_context(query=query, n_results=top_k))
    query_results = []
    per_source = defaultdict(lambda: {"expected_queries": 0, "hit_queries": 0})

    for case in cases:
        query = case["query"]
        expected_relevance = expected_relevance_for_case(case)
        matches = retriever(query, k)
        metrics = evaluate_retrieved_matches(matches, expected_relevance, k=k)
        query_results.append({"query": query, **metrics})

        for source in expected_relevance:
            per_source[source]["expected_queries"] += 1
            if source in metrics["found_sources"]:
                per_source[source]["hit_queries"] += 1

    total = len(query_results) or 1
    aggregate = {
        "queries": len(query_results),
        "top_k": k,
        "hit_rate_at_k": round(sum(item["hit_rate_at_k"] for item in query_results) / total, 4),
        "recall_at_k": round(sum(item["recall_at_k"] for item in query_results) / total, 4),
        "precision_at_k": round(sum(item["precision_at_k"] for item in query_results) / total, 4),
        "mrr": round(sum(item["mrr"] for item in query_results) / total, 4),
        "ndcg_at_k": round(sum(item["ndcg_at_k"] for item in query_results) / total, 4),
    }
    source_metrics = {
        source: {
            **values,
            "recall_at_k": round(values["hit_queries"] / values["expected_queries"], 4)
            if values["expected_queries"]
            else 0.0,
        }
        for source, values in sorted(per_source.items())
    }
    return {"aggregate": aggregate, "per_source": source_metrics, "queries": query_results}


def quality_gate_passed(
    aggregate: dict[str, float],
    min_hit_rate: float = 0.8,
    min_recall: float = 0.7,
    min_precision: float = 0.5,
    min_mrr: float = 0.7,
    min_ndcg: float = 0.7,
) -> tuple[bool, list[str]]:
    thresholds = {
        "hit_rate_at_k": min_hit_rate,
        "recall_at_k": min_recall,
        "precision_at_k": min_precision,
        "mrr": min_mrr,
        "ndcg_at_k": min_ndcg,
    }
    failures = [
        f"{metric}={aggregate.get(metric, 0.0):.4f} below threshold {threshold:.4f}"
        for metric, threshold in thresholds.items()
        if aggregate.get(metric, 0.0) < threshold
    ]
    return not failures, failures


def _match_source(match: dict[str, Any]) -> str:
    metadata = match.get("metadata") if isinstance(match.get("metadata"), dict) else {}
    return normalize_source_name(str(metadata.get("source") or metadata.get("file_name") or match.get("source", "")))
