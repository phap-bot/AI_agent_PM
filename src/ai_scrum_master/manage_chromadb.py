from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from ai_scrum_master.core.config import BASE_DIR, get_settings
from ai_scrum_master.ingestion.ingest import ingest_raw_docs
from ai_scrum_master.retrieval.vector_store import get_chroma_client, get_persist_directory

CANONICAL_RAW_DOCS_DIR = BASE_DIR / "data" / "raw_docs"
SWE_BENCH_RAW_DOCS_DIR = CANONICAL_RAW_DOCS_DIR / "swe_bench_issues"

KNOWN_CHROMA_DIRS = (
    BASE_DIR / "data" / "chromadb",
    BASE_DIR / "data" / "swe_bench_chromadb",
)


def known_chroma_dirs() -> list[Path]:
    seen: set[Path] = set()
    dirs: list[Path] = []
    for path in KNOWN_CHROMA_DIRS:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            dirs.append(resolved)
    return dirs


def list_collections(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(path))
        return [
            {"name": collection.name, "count": collection.count()}
            for collection in client.list_collections()
        ]
    except BaseException as exc:
        return [{"error": f"{type(exc).__name__}: {exc}"}]


def build_state() -> dict[str, Any]:
    settings = get_settings()
    canonical_dir = get_persist_directory()
    return {
        "canonical_persist_dir": str(canonical_dir),
        "canonical_collection": settings.context_collection,
        "raw_docs_dir": str(CANONICAL_RAW_DOCS_DIR.resolve()),
        "swe_bench_raw_docs_dir": str(SWE_BENCH_RAW_DOCS_DIR.resolve()),
        "swe_bench_markdown_files": len(list(SWE_BENCH_RAW_DOCS_DIR.glob("*.md"))) if SWE_BENCH_RAW_DOCS_DIR.exists() else 0,
        "known_dirs": [
            {
                "path": str(path),
                "exists": path.exists(),
                "canonical": path == canonical_dir,
                "collections": list_collections(path),
            }
            for path in known_chroma_dirs()
        ],
    }


def print_state() -> None:
    print(json.dumps(build_state(), ensure_ascii=False, indent=2))


def require_yes(args: argparse.Namespace, action: str) -> None:
    if not getattr(args, "yes", False):
        raise SystemExit(f"Refusing to {action} without --yes")


def remove_known_dirs() -> tuple[list[str], list[dict[str, str]]]:
    removed = []
    failed = []
    for path in known_chroma_dirs():
        if not path.exists():
            continue
        try:
            shutil.rmtree(path)
            removed.append(str(path))
        except PermissionError as exc:
            failed.append({"path": str(path), "error": f"{type(exc).__name__}: {exc}"})
    return removed, failed


def reset(args: argparse.Namespace) -> int:
    require_yes(args, "reset ChromaDB directories")
    before = [
        {"path": str(path), "exists": path.exists(), "canonical": path == get_persist_directory()}
        for path in known_chroma_dirs()
    ]
    removed, failed = remove_known_dirs()
    report = {
        "status": "failed" if failed else "reset",
        "canonical_collection": get_settings().context_collection,
        "before": before,
        "removed": removed,
        "failed": failed,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if failed else 0


def rebuild(args: argparse.Namespace) -> int:
    require_yes(args, "reset and rebuild ChromaDB")
    removed, failed = remove_known_dirs()
    if failed:
        report = {
            "status": "failed",
            "removed": removed,
            "failed": failed,
            "hint": "Close any Python/FastAPI/Streamlit process using ChromaDB, then rerun rebuild.",
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1
    result = ingest_raw_docs(raw_docs_dir=Path(args.raw_docs_dir) if args.raw_docs_dir else None)
    report = {
        "status": "rebuilt",
        "removed": removed,
        "ingest": result,
        "state": build_state(),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def verify(_: argparse.Namespace) -> int:
    settings = get_settings()
    canonical_dir = get_persist_directory()
    state = build_state()
    errors = []

    if settings.context_collection != "ai_scrum_master_context":
        errors.append(f"Unexpected CHROMA_COLLECTION={settings.context_collection}")
    if canonical_dir != (BASE_DIR / "data" / "chromadb").resolve():
        errors.append(f"Unexpected CHROMA_PERSIST_DIR={canonical_dir}")

    legacy_existing = [
        entry["path"]
        for entry in state["known_dirs"]
        if entry["exists"] and not entry["canonical"]
    ]
    if legacy_existing:
        errors.append(f"Legacy Chroma dirs still exist: {legacy_existing}")

    try:
        client = get_chroma_client()
        collections = {collection.name: collection.count() for collection in client.list_collections()}
    except BaseException as exc:
        errors.append(f"Could not list canonical collections: {type(exc).__name__}: {exc}")
        collections = {}

    unexpected_collections = [name for name in collections if name != settings.context_collection]
    if unexpected_collections:
        errors.append(f"Unexpected collections in canonical DB: {unexpected_collections}")
    if settings.context_collection not in collections:
        errors.append(f"Canonical collection missing: {settings.context_collection}")

    report = {
        "status": "failed" if errors else "ok",
        "errors": errors,
        "collections": collections,
        "state": state,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage ChromaDB under src/ai_scrum_master/data only.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List known in-package Chroma directories and collections.")

    reset_parser = subparsers.add_parser("reset", help="Delete known in-package Chroma directories.")
    reset_parser.add_argument("--yes", action="store_true", help="Confirm destructive reset.")

    rebuild_parser = subparsers.add_parser("rebuild", help="Reset and ingest raw docs into canonical collection.")
    rebuild_parser.add_argument("--yes", action="store_true", help="Confirm destructive rebuild.")
    rebuild_parser.add_argument("--raw-docs-dir", default="", help="Optional raw docs directory override.")

    subparsers.add_parser("verify", help="Verify canonical DB/collection state.")

    args = parser.parse_args()
    if args.command == "list":
        print_state()
        return 0
    if args.command == "reset":
        return reset(args)
    if args.command == "rebuild":
        return rebuild(args)
    if args.command == "verify":
        return verify(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
