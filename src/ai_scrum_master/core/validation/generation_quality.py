from __future__ import annotations

from typing import Any

from ai_scrum_master.retrieval.rag import citation_id_for_match


def evaluate_grounded_generation(answer: dict[str, Any], matches: list[dict[str, Any]]) -> dict[str, Any]:
    valid_citations = {citation_id_for_match(match) for match in matches}
    cited = [normalize_citation(str(citation)) for citation in answer.get("citations", []) if str(citation).strip()]
    cited_set = set(cited)
    valid_cited = cited_set & valid_citations
    unsupported_claims = [
        str(claim)
        for claim in answer.get("unsupported_claims", [])
        if str(claim).strip()
    ]
    status = str(answer.get("status") or "").upper()

    citation_precision = len(valid_cited) / len(cited_set) if cited_set else 0.0
    citation_recall_at_retrieved = len(valid_cited) / len(valid_citations) if valid_citations else 0.0
    answer_has_citation = bool(cited_set)
    grounded = (
        status == "ANSWERED"
        and answer_has_citation
        and citation_precision == 1.0
        and not unsupported_claims
    )

    return {
        "status": status,
        "grounded": grounded,
        "answer_has_citation": answer_has_citation,
        "citation_precision": round(citation_precision, 4),
        "citation_recall_at_retrieved": round(citation_recall_at_retrieved, 4),
        "unsupported_claim_count": len(unsupported_claims),
        "invalid_citations": sorted(cited_set - valid_citations),
        "valid_citations": sorted(valid_cited),
    }


def generation_quality_gate_passed(
    metrics: dict[str, Any],
    min_citation_precision: float = 1.0,
    allow_unsupported_claims: bool = False,
) -> tuple[bool, list[str]]:
    failures = []
    if not metrics.get("answer_has_citation"):
        failures.append("answer_has_citation=false")
    if metrics.get("citation_precision", 0.0) < min_citation_precision:
        failures.append(
            f"citation_precision={metrics.get('citation_precision', 0.0):.4f} below threshold {min_citation_precision:.4f}"
        )
    if metrics.get("unsupported_claim_count", 0) and not allow_unsupported_claims:
        failures.append(f"unsupported_claim_count={metrics.get('unsupported_claim_count', 0)}")
    if metrics.get("invalid_citations"):
        failures.append(f"invalid_citations={metrics['invalid_citations']}")
    return not failures, failures


def normalize_citation(citation: str) -> str:
    value = citation.strip()
    for prefix in ("chunk_id=", "CITATION_ID:", "citation_id:", "id="):
        if value.lower().startswith(prefix.lower()):
            return value[len(prefix):].strip()
    return value
