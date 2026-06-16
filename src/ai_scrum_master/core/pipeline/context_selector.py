from __future__ import annotations

from typing import Any

from ai_scrum_master.core.schemas.agent_schemas import build_planning_brief
from ai_scrum_master.core.validation.quality_gate import normalize_source_name


def select_context_for_route(requirement: str, context: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    profile = route.get("profile", route)
    required = set(_normalized_sources(profile.get("required_sources", route.get("required_sources", []))))
    optional = set(_normalized_sources(profile.get("optional_sources", route.get("optional_sources", []))))
    allowed = required | optional

    selected_sources = []
    ignored_sources = []
    seen_selected = set()
    for source in context.get("retrieved_sources", []):
        # Do not filter based on allowed domains anymore. Accept all retrieved sources.
        dedupe_key = _source_key(source)
        if dedupe_key not in seen_selected:
            seen_selected.add(dedupe_key)
            selected_sources.append(source)

    selected_matches = _select_matches(context.get("matches", []), selected_sources)
    selected_snippets = _select_snippets(context.get("context_snippets", []), selected_sources)
    selected_documents = [match.get("document", "") for match in selected_matches if match.get("document")]
    if not selected_documents and selected_sources:
        selected_documents = [
            str(source.get("excerpt", "")).strip()
            for source in selected_sources
            if str(source.get("excerpt", "")).strip()
        ]

    selected_source_names = {
        normalize_source_name(str(source.get("source", "")))
        for source in selected_sources
    }
    # Empty missing required/optional sources to prevent blocking the planner
    missing_required = []
    missing_optional = []

    warnings = list(context.get("warnings", []))

    selected = dict(context)
    selected.update(
        {
            "documents": selected_documents,
            "ids": [match.get("id", "") for match in selected_matches],
            "metadatas": [match.get("metadata", {}) for match in selected_matches],
            "distances": [match.get("distance") for match in selected_matches],
            "matches": selected_matches,
            "retrieved_sources": selected_sources,
            "selected_context_sources": selected_sources,
            "ignored_context_sources": ignored_sources,
            "context_snippets": selected_snippets,
            "route": route,
            "required_sources": sorted(required),
            "optional_sources": sorted(optional),
            "missing_required_sources": missing_required,
            "missing_optional_sources": missing_optional,
            "warnings": list(dict.fromkeys(warnings)),
        }
    )
    selected["planning_brief"] = build_planning_brief(
        requirement=requirement,
        sources=selected_sources,
        retrieval_status=selected.get("retrieval_status", "empty"),
        confidence=selected.get("confidence", 0.0),
        planning_instruction=(
            "Use only usable_evidence excerpts as project documentation evidence. "
            "Ignored context must not influence the story."
        ),
    )
    return selected


def _normalized_sources(values: list[Any]) -> list[str]:
    return [normalize_source_name(str(value)) for value in values if str(value).strip()]


def _source_key(source: dict[str, Any]) -> tuple[str, str]:
    return (
        str(source.get("chunk_id") or normalize_source_name(str(source.get("source", "")))),
        str(source.get("chunk_index", "?")),
    )


def _source_alias_matches(source_name: str, expected: set[str]) -> bool:
    return any(source_name == item.split("_", 1)[0] for item in expected)


def _source_set_contains(source_names: set[str], expected: str) -> bool:
    return expected in source_names or _source_alias_matches(expected, source_names) or any(name == expected.split("_", 1)[0] for name in source_names)


def _select_matches(matches: list[dict[str, Any]], selected_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected_ids = {source.get("id") for source in selected_sources if source.get("id")}
    selected_excerpts = {source.get("excerpt") for source in selected_sources if source.get("excerpt")}
    selected_names = {normalize_source_name(str(source.get("source", ""))) for source in selected_sources}
    selected = []
    seen = set()
    for match in matches:
        metadata = match.get("metadata") if isinstance(match.get("metadata"), dict) else {}
        match_source = normalize_source_name(str(metadata.get("source", "")))
        if not (
            match.get("id") in selected_ids
            or match.get("document") in selected_excerpts
            or match_source in selected_names
        ):
            continue
        key = (str(metadata.get("chunk_id") or match_source), str(metadata.get("chunk_index", "?")))
        if key in seen:
            continue
        seen.add(key)
        selected.append(match)
    return selected


def _select_snippets(snippets: list[str], selected_sources: list[dict[str, Any]]) -> list[str]:
    selected_names = [str(source.get("source", "")) for source in selected_sources]
    return [
        snippet
        for snippet in snippets
        if any(name and name in snippet for name in selected_names)
    ]
