from __future__ import annotations

import argparse
import json
from typing import Any

from ai_scrum_master.retrieval.vector_store import search_context


def compact_match(match: dict[str, Any], rank: int, excerpt_chars: int, show_id: bool = False) -> dict[str, Any]:
    metadata = match.get("metadata") if isinstance(match.get("metadata"), dict) else {}
    document = " ".join(str(match.get("document") or "").split())
    payload = {
        "rank": rank,
        "score": match.get("score"),
        "source": metadata.get("source") or metadata.get("file_name") or "unknown",
        "chunk": metadata.get("chunk_index", "?"),
        "excerpt": document[:excerpt_chars],
    }
    if show_id:
        payload["id"] = match.get("id") or metadata.get("chunk_id") or metadata.get("id") or ""
    return payload


def print_table(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        print(f"{row['rank']}. score={row['score']} source={row['source']} chunk={row['chunk']}")
        if row.get("id"):
            print(f"   id={row['id']}")
        print(f"   {row['excerpt']}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Query canonical AI Scrum Master ChromaDB with compact output.")
    parser.add_argument("query", help="Text query to search in the canonical Chroma collection.")
    parser.add_argument("--k", type=int, default=3, help="Number of final matches to print.")
    parser.add_argument("--chars", type=int, default=220, help="Excerpt characters per match.")
    parser.add_argument("--show-id", action="store_true", help="Include chunk ID in output.")
    parser.add_argument("--json", action="store_true", help="Print compact JSON instead of table text.")
    args = parser.parse_args()

    matches = search_context(args.query, n_results=args.k)
    rows = [
        compact_match(match, rank=index, excerpt_chars=args.chars, show_id=args.show_id)
        for index, match in enumerate(matches, start=1)
    ]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print_table(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
