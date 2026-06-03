from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DATASET_SERVER_BASE_URL = "https://datasets-server.huggingface.co"
DEFAULT_DATASET = "princeton-nlp/SWE-bench"
DEFAULT_CONFIG = "default"
DEFAULT_SPLIT = "test"
DEFAULT_CACHE_DIR = Path("src/ai_scrum_master/data/hf_cache")


def fetch_rows(
    dataset: str = DEFAULT_DATASET,
    config: str = DEFAULT_CONFIG,
    split: str = DEFAULT_SPLIT,
    offset: int = 0,
    length: int = 50,
    timeout: int = 120,
    source: str = "auto",
    parquet_path: Path | None = None,
    cache_dir: Path = DEFAULT_CACHE_DIR,
) -> list[dict[str, Any]]:
    source = source.strip().lower()
    viewer_error: Exception | None = None
    if source in {"auto", "dataset-viewer"}:
        try:
            return fetch_rows_from_dataset_viewer(
                dataset=dataset,
                config=config,
                split=split,
                offset=offset,
                length=length,
                timeout=timeout,
            )
        except Exception as exc:
            viewer_error = exc
            if source == "dataset-viewer":
                raise RuntimeError(
                    "Hugging Face Dataset Viewer failed. Try --source parquet or pass --parquet-path."
                ) from exc

    if source not in {"auto", "parquet"}:
        raise ValueError("source must be one of: auto, dataset-viewer, parquet")

    try:
        return fetch_rows_from_parquet(
            dataset=dataset,
            split=split,
            offset=offset,
            length=length,
            timeout=timeout,
            parquet_path=parquet_path,
            cache_dir=cache_dir,
        )
    except Exception as parquet_error:
        if viewer_error is not None:
            raise RuntimeError(
                "Unable to fetch SWE-bench rows from Dataset Viewer or parquet fallback. "
                "If your network resets Hugging Face downloads, manually download "
                "https://huggingface.co/datasets/princeton-nlp/SWE-bench/tree/main/data "
                "and rerun with --parquet-path path\\to\\test-00000-of-00001.parquet."
            ) from parquet_error
        raise


def fetch_rows_from_dataset_viewer(
    dataset: str,
    config: str,
    split: str,
    offset: int,
    length: int,
    timeout: int,
) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode(
        {
            "dataset": dataset,
            "config": config,
            "split": split,
            "offset": offset,
            "length": length,
        }
    )
    url = f"{DATASET_SERVER_BASE_URL}/rows?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "ai-scrum-master-swe-bench-sampler"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    rows = payload.get("rows", [])
    return [item.get("row", {}) for item in rows if isinstance(item, dict)]


def fetch_rows_from_parquet(
    dataset: str,
    split: str,
    offset: int,
    length: int,
    timeout: int,
    parquet_path: Path | None = None,
    cache_dir: Path = DEFAULT_CACHE_DIR,
) -> list[dict[str, Any]]:
    import pandas as pd

    path = parquet_path or download_parquet_file(
        dataset=dataset,
        split=split,
        cache_dir=cache_dir,
        timeout=timeout,
    )
    frame = pd.read_parquet(path)
    rows = frame.iloc[offset : offset + length].to_dict(orient="records")
    return [dict(row) for row in rows]


def download_parquet_file(
    dataset: str,
    split: str,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    timeout: int = 120,
    retries: int = 3,
) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{split}-00000-of-00001.parquet"
    target = cache_dir / f"{safe_filename(dataset)}__{filename}"
    if target.exists() and target.stat().st_size > 0:
        return target

    try:
        return download_parquet_file_with_hf_hub(
            dataset=dataset,
            split=split,
            cache_dir=cache_dir,
        )
    except Exception:
        pass

    url = f"https://huggingface.co/datasets/{dataset}/resolve/main/data/{filename}"
    temp_target = target.with_suffix(".parquet.tmp")
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "ai-scrum-master-swe-bench-sampler"})
            with urllib.request.urlopen(request, timeout=timeout) as response, temp_target.open("wb") as file:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    file.write(chunk)
            temp_target.replace(target)
            return target
        except (ConnectionResetError, TimeoutError, urllib.error.URLError, OSError) as exc:
            last_error = exc
            if temp_target.exists():
                temp_target.unlink(missing_ok=True)
            if attempt < retries:
                time.sleep(min(2 * attempt, 8))

    raise RuntimeError(f"Could not download SWE-bench parquet file from {url}") from last_error


def download_parquet_file_with_hf_hub(dataset: str, split: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> Path:
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from huggingface_hub import hf_hub_download

    filename = f"{split}-00000-of-00001.parquet"
    path = hf_hub_download(
        repo_id=dataset,
        repo_type="dataset",
        filename=f"data/{filename}",
        local_dir=str(cache_dir),
    )
    return Path(path)


def normalize_case(row: dict[str, Any], index: int) -> dict[str, Any]:
    instance_id = str(row.get("instance_id") or f"swe-bench-{index:03d}")
    return {
        "sample_index": index,
        "dataset": DEFAULT_DATASET,
        "instance_id": instance_id,
        "repo": str(row.get("repo") or ""),
        "base_commit": str(row.get("base_commit") or ""),
        "environment_setup_commit": str(row.get("environment_setup_commit") or ""),
        "created_at": str(row.get("created_at") or ""),
        "version": str(row.get("version") or ""),
        "problem_statement": sanitize_issue_text(str(row.get("problem_statement") or "")).strip(),
        "hints_text": sanitize_issue_text(str(row.get("hints_text") or "")).strip(),
        "fail_to_pass": parse_test_list(row.get("FAIL_TO_PASS")),
        "pass_to_pass": parse_test_list(row.get("PASS_TO_PASS")),
        "patch_chars": len(str(row.get("patch") or "")),
        "test_patch_chars": len(str(row.get("test_patch") or "")),
    }


def sanitize_issue_text(text: str) -> str:
    def replace_patch_block(match: re.Match[str]) -> str:
        language = match.group("language").strip().lower()
        body = match.group("body")
        if language in {"diff", "patch"} or re.search(r"(^|\n)diff --git ", body):
            return "```text\n[Patch diff omitted from benchmark requirement.]\n```"
        return match.group(0)

    return re.sub(
        r"```(?P<language>[^\r\n`]*)\r?\n(?P<body>.*?)```",
        replace_patch_block,
        text,
        flags=re.DOTALL,
    )


def parse_test_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if not isinstance(value, str) or not value.strip():
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return [value.strip()]
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return [str(parsed)]


def markdown_for_case(case: dict[str, Any]) -> str:
    title = first_nonempty_line(case["problem_statement"]) or case["instance_id"]
    return "\n".join(
        [
            f"# SWE-bench Issue: {case['instance_id']}",
            "",
            f"- Dataset: {case['dataset']}",
            f"- Repository: {case['repo']}",
            f"- Instance ID: {case['instance_id']}",
            f"- Base Commit: {case['base_commit']}",
            f"- Environment Setup Commit: {case['environment_setup_commit']}",
            f"- Created At: {case['created_at']}",
            f"- Version: {case['version']}",
            "",
            "## Issue Title",
            title,
            "",
            "## Problem Statement",
            case["problem_statement"] or "No problem statement provided.",
            "",
            "## Issue Discussion Hints",
            case["hints_text"] or "No issue discussion hints provided.",
            "",
            "## Failing Tests That Should Pass",
            bullet_list(case["fail_to_pass"]),
            "",
            "## Existing Passing Tests To Preserve",
            bullet_list(case["pass_to_pass"]),
            "",
            "## Planning Guidance",
            (
                "Treat this as a real GitHub issue requirement. Create planning output from the issue text, "
                "repository context, failing tests, and hints only. Do not infer implementation details from "
                "the hidden gold patch."
            ),
            "",
        ]
    )


def first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip(" #\t")
        if line:
            return line
    return ""


def bullet_list(items: list[str]) -> str:
    if not items:
        return "- None provided."
    return "\n".join(f"- `{item}`" for item in items)


def safe_filename(value: str, max_length: int = 120) -> str:
    value = value.replace("/", "__")
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    value = value.strip("._")
    return (value or "swe_bench_issue")[:max_length]


def write_sample_outputs(
    cases: list[dict[str, Any]],
    output_dir: Path,
    raw_docs_dir: Path,
    write_raw_docs: bool = True,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_docs_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = output_dir / "swe_bench_first50.jsonl"
    planner_cases_path = output_dir / "planner_cases_first50.json"
    retrieval_cases_path = output_dir / "retrieval_cases_first50.json"
    markdown_paths = []
    planner_cases = []
    retrieval_cases = []

    with jsonl_path.open("w", encoding="utf-8") as file:
        for case in cases:
            file.write(json.dumps(case, ensure_ascii=False) + "\n")

    for case in cases:
        filename = f"swe_bench_{case['sample_index']:03d}_{safe_filename(case['instance_id'])}.md"
        source_stem = Path(filename).stem
        planner_cases.append(
            {
                "id": case["instance_id"],
                "requirement": case["problem_statement"],
                "expected_status": "READY",
                "expected_sources": [source_stem],
            }
        )
        retrieval_cases.append({"query": case["problem_statement"], "expected_sources": [source_stem]})
        if write_raw_docs:
            path = raw_docs_dir / filename
            path.write_text(markdown_for_case(case), encoding="utf-8")
            markdown_paths.append(str(path))

    planner_cases_path.write_text(json.dumps(planner_cases, ensure_ascii=False, indent=2), encoding="utf-8")
    retrieval_cases_path.write_text(json.dumps(retrieval_cases, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "cases": len(cases),
        "jsonl_path": str(jsonl_path),
        "planner_cases_path": str(planner_cases_path),
        "retrieval_cases_path": str(retrieval_cases_path),
        "raw_docs_dir": str(raw_docs_dir),
        "markdown_files": len(markdown_paths),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch the first N SWE-bench rows and prepare RAG raw docs.")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--split", default=DEFAULT_SPLIT)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--source", choices=["auto", "dataset-viewer", "parquet"], default="auto")
    parser.add_argument("--parquet-path", default="")
    parser.add_argument("--cache-dir", default=str(DEFAULT_CACHE_DIR))
    parser.add_argument("--output-dir", default="src/ai_scrum_master/data/swe_bench_sample")
    parser.add_argument("--raw-docs-dir", default="src/ai_scrum_master/data/raw_docs/swe_bench_issues")
    parser.add_argument("--no-raw-docs", action="store_true")
    args = parser.parse_args()

    try:
        rows = fetch_rows(
            dataset=args.dataset,
            config=args.config,
            split=args.split,
            offset=args.offset,
            length=args.limit,
            source=args.source,
            parquet_path=Path(args.parquet_path) if args.parquet_path else None,
            cache_dir=Path(args.cache_dir),
        )
    except Exception as exc:
        filename = f"{args.split}-00000-of-00001.parquet"
        report = {
            "status": "failed",
            "error": str(exc),
            "manual_download_url": f"https://huggingface.co/datasets/{args.dataset}/blob/main/data/{filename}",
            "retry_with_local_file": (
                "python.exe -m ai_scrum_master.datasets.swe_bench_sample "
                f"--source parquet --parquet-path path\\to\\{filename} --limit {args.limit}"
            ),
        }
        print(json.dumps(report, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    cases = [normalize_case(row, args.offset + index) for index, row in enumerate(rows)]
    report = write_sample_outputs(
        cases=cases,
        output_dir=Path(args.output_dir),
        raw_docs_dir=Path(args.raw_docs_dir),
        write_raw_docs=not args.no_raw_docs,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
