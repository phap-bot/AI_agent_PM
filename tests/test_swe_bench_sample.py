from pathlib import Path

from ai_scrum_master.datasets.swe_bench_sample import (
    fetch_rows,
    markdown_for_case,
    normalize_case,
    sanitize_issue_text,
    safe_filename,
    write_sample_outputs,
)


def test_normalize_swe_bench_case_preserves_issue_fields_without_gold_patch_text() -> None:
    row = {
        "repo": "sqlfluff/sqlfluff",
        "instance_id": "sqlfluff__sqlfluff-4764",
        "base_commit": "abc123",
        "patch": "diff --git a/source.py b/source.py",
        "test_patch": "diff --git a/test.py b/test.py",
        "problem_statement": "Enable quiet mode\n\nCLI should support less verbose output.",
        "hints_text": "This matters for pre-commit.",
        "FAIL_TO_PASS": '["test_cli.py::test_quiet"]',
        "PASS_TO_PASS": ["test_cli.py::test_existing"],
    }

    case = normalize_case(row, 0)
    markdown = markdown_for_case(case)

    assert case["repo"] == "sqlfluff/sqlfluff"
    assert case["fail_to_pass"] == ["test_cli.py::test_quiet"]
    assert case["patch_chars"] > 0
    assert "Enable quiet mode" in markdown
    assert "test_cli.py::test_quiet" in markdown
    assert "diff --git" not in markdown


def test_safe_filename_removes_path_separators() -> None:
    assert safe_filename("owner/repo issue #1") == "owner__repo_issue_1"


def test_sanitize_issue_text_removes_patch_blocks_but_keeps_repro_code() -> None:
    text = """Bug report

```python
print("repro")
```

```diff
diff --git a/file.py b/file.py
+solution()
```
"""

    sanitized = sanitize_issue_text(text)

    assert 'print("repro")' in sanitized
    assert "diff --git" not in sanitized
    assert "Patch diff omitted" in sanitized


def test_write_sample_outputs_creates_planner_and_retrieval_cases(tmp_path: Path) -> None:
    case = normalize_case(
        {
            "repo": "django/django",
            "instance_id": "django__django-100",
            "problem_statement": "Fix migration crash",
            "FAIL_TO_PASS": [],
            "PASS_TO_PASS": [],
        },
        0,
    )

    report = write_sample_outputs([case], tmp_path / "sample", tmp_path / "raw_docs")

    assert report["cases"] == 1
    assert Path(report["planner_cases_path"]).exists()
    assert Path(report["retrieval_cases_path"]).exists()
    assert report["markdown_files"] == 1


def test_fetch_rows_auto_falls_back_to_parquet(monkeypatch, tmp_path: Path) -> None:
    from ai_scrum_master.datasets import swe_bench_sample

    def fail_viewer(**kwargs):
        raise ConnectionResetError("reset")

    def fake_parquet(**kwargs):
        assert kwargs["cache_dir"] == tmp_path
        return [{"instance_id": "django__django-100", "problem_statement": "Fix migration crash"}]

    monkeypatch.setattr(swe_bench_sample, "fetch_rows_from_dataset_viewer", fail_viewer)
    monkeypatch.setattr(swe_bench_sample, "fetch_rows_from_parquet", fake_parquet)

    rows = fetch_rows(source="auto", cache_dir=tmp_path)

    assert rows == [{"instance_id": "django__django-100", "problem_statement": "Fix migration crash"}]
