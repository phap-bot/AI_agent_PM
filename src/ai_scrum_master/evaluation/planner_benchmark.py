from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from collections import Counter
from statistics import mean
from typing import Any

from ai_scrum_master.agents.evaluator import EvaluatorAgent
from ai_scrum_master.agents.planner import PlannerAgent
from ai_scrum_master.agents.researcher import ResearcherAgent
from ai_scrum_master.core.validation.quality import (
    domain_contamination_issues,
    is_generic_acceptance_criterion,
    is_placeholder_task,
)
from ai_scrum_master.core.validation.story_validator import evaluate_planner_output, has_actionable_task, similar_item_pairs


def load_cases(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_cases(cases: list[dict[str, Any]], offset: int = 0, limit: int = 0) -> list[dict[str, Any]]:
    selected = cases[max(offset, 0) :]
    if limit > 0:
        selected = selected[:limit]
    return selected


def route_for_benchmark_case(case: dict[str, Any]) -> dict[str, Any]:
    expected_sources = list(case.get("expected_sources", []))
    return {
        "domain": "benchmark_case",
        "story_type": "software_feature",
        "required_sources": expected_sources,
        "optional_sources": [],
        "required_concepts": [],
        "forbidden_domains": [],
        "template_name": "swe_bench_case",
        "profile": {
            "required_sources": expected_sources,
            "optional_sources": [],
            "required_concepts": [],
            "forbidden_domains": [],
            "template_name": "swe_bench_case",
        },
        "reason": "Benchmark case provides expected source files.",
        "reasoning": "Benchmark case provides expected source files.",
    }


def gwt_count(criteria: list[str]) -> int:
    return sum(
        1
        for criterion in criteria
        if isinstance(criterion, str)
        and "given" in criterion.lower()
        and "when" in criterion.lower()
        and "then" in criterion.lower()
        and criterion.lower().find("given") < criterion.lower().find("when") < criterion.lower().find("then")
    )


def task_group_ready(tasks: dict[str, Any], group: str) -> bool:
    return isinstance(tasks.get(group), list) and bool(tasks.get(group))


def score_story(case: dict[str, Any], context: dict[str, Any], story: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
    criteria = story.get("acceptance_criteria", [])
    tasks = story.get("tasks", {}) if isinstance(story.get("tasks"), dict) else {}
    dod = story.get("definition_of_done", [])
    expected_sources = set(case.get("expected_sources", []))
    actual_sources = {source.get("source") for source in context.get("retrieved_sources", []) if isinstance(source, dict)}
    context_hit = bool(expected_sources & actual_sources) if expected_sources else bool(actual_sources)
    if not context_hit and expected_sources:
        context_hit = any(
            expected in str(actual_source)
            for expected in expected_sources
            for actual_source in actual_sources
        )
    be_ready = task_group_ready(tasks, "be")
    fe_ready = task_group_ready(tasks, "fe")
    qa_ready = task_group_ready(tasks, "qa")
    task_groups_ready = all((be_ready, fe_ready, qa_ready))
    gwt_ready = len(criteria) >= 3 and gwt_count(criteria) >= 3
    dod_ready = len(dod) >= 4
    expected_status = case.get("expected_status", "READY")

    components = {
        "retrieval_context": 15 if context_hit else 0,
        "planning_status": 15 if story.get("planning_status") == expected_status else 0,
        "acceptance_criteria": 20 if gwt_ready else max(0, min(15, gwt_count(criteria) * 5)),
        "tasks": 15 if task_groups_ready else sum(5 for group in ("be", "fe", "qa") if tasks.get(group)),
        "definition_of_done": 15 if dod_ready else min(10, len(dod) * 2.5),
        "evaluation": 20 if evaluation.get("status") == "APPROVED" else 0,
    }
    return {
        "score": round(sum(components.values()), 2),
        "components": components,
        "context_hit": context_hit,
        "gwt_count": gwt_count(criteria),
        "ac_count": len(criteria),
        "task_groups_ready": task_groups_ready,
        "be_ready": be_ready,
        "fe_ready": fe_ready,
        "qa_ready": qa_ready,
        "dod_count": len(dod),
    }


def retrieval_is_ok(result: dict[str, Any]) -> bool:
    return str(result.get("retrieval_status") or "").lower() == "ok"


def _collect_text_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        texts = []
        for item in value:
            texts.extend(_collect_text_values(item))
        return texts
    if isinstance(value, dict):
        texts = []
        for item in value.values():
            texts.extend(_collect_text_values(item))
        return texts
    return []


def timeout_or_pipeline_failure(result: dict[str, Any]) -> bool:
    if result.get("timed_out") or result.get("failure_type"):
        return True
    story = result.get("story", {}) if isinstance(result.get("story"), dict) else {}
    context = result.get("context", {}) if isinstance(result.get("context"), dict) else {}
    if story.get("timed_out") or story.get("failure_type") or context.get("failure_type"):
        return True
    failure_terms = ("timeout", "timed out", "context too long", "prompt too long", "exception", "traceback", "planner_exception", "planner_timeout")
    text = "\n".join(
        _collect_text_values(
            {
                "warnings": result.get("warnings", []),
                "story_warnings": result.get("story", {}).get("warnings", []) if isinstance(result.get("story"), dict) else [],
                "context_warnings": result.get("context", {}).get("warnings", []) if isinstance(result.get("context"), dict) else [],
                "evaluation_warnings": result.get("evaluation", {}).get("warnings", []) if isinstance(result.get("evaluation"), dict) else [],
                "evaluation_issues": result.get("evaluation_issues", []),
            }
        )
    ).lower()
    return any(term in text for term in failure_terms)


def _case_requirement(result: dict[str, Any], story: dict[str, Any]) -> str:
    case = result.get("case", {}) if isinstance(result.get("case"), dict) else {}
    return str(case.get("requirement") or story.get("requirement") or story.get("title") or result.get("case_id", ""))


def _story_tasks(story: dict[str, Any]) -> dict[str, Any]:
    return story.get("tasks", {}) if isinstance(story.get("tasks"), dict) else {}


def _story_has_generic_output(story: dict[str, Any]) -> bool:
    criteria = story.get("acceptance_criteria", [])
    if any(is_generic_acceptance_criterion(criterion) for criterion in criteria if isinstance(criterion, str)):
        return True
    tasks = _story_tasks(story)
    return any(
        is_placeholder_task(task)
        for group in ("be", "fe", "qa")
        for task in (tasks.get(group, []) if isinstance(tasks.get(group), list) else [])
    )


def _story_has_non_actionable_task(story: dict[str, Any]) -> bool:
    tasks = _story_tasks(story)
    return any(not has_actionable_task(tasks.get(group), group=group) for group in ("be", "fe", "qa"))


def _deterministic_validation(result: dict[str, Any], story: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    requirement = _case_requirement(result, story)
    if not story:
        return {"passed": False, "failures": ["missing_story"], "metrics": {}}
    return evaluate_planner_output(requirement, story, context)


def _evaluator_warning_contradicts_approval(result: dict[str, Any]) -> bool:
    if result.get("evaluation_status") != "APPROVED":
        return False
    evaluation = result.get("evaluation", {}) if isinstance(result.get("evaluation"), dict) else {}
    warning_text = "\n".join(_collect_text_values({"warnings": evaluation.get("warnings", []), "issues": result.get("evaluation_issues", [])})).lower()
    contradiction_terms = ("revision", "fail", "invalid", "missing", "generic", "placeholder", "not ready", "must")
    return any(term in warning_text for term in contradiction_terms)


def build_classification_flags(result: dict[str, Any]) -> dict[str, bool]:
    score = result.get("score", {}) if isinstance(result.get("score"), dict) else {}
    story = result.get("story", {}) if isinstance(result.get("story"), dict) else {}
    context = result.get("context", {}) if isinstance(result.get("context"), dict) else {}
    has_expected_sources = bool(result.get("case", {}).get("expected_sources", [])) if isinstance(result.get("case"), dict) else False
    requirement = _case_requirement(result, story)
    domain_issues = domain_contamination_issues(expected_domain, requirement, story) if story else []
    validation = _deterministic_validation(result, story, context)
    similar_pairs = similar_item_pairs(story.get("acceptance_criteria", [])) if story else []
    return {
        "retrieval_ok": retrieval_is_ok(result),
        "evaluation_approved": result.get("evaluation_status") == "APPROVED",
        "planning_ready": story.get("planning_status") == "READY",
        "context_hit": bool(score.get("context_hit")),
        "has_min_ac": int(score.get("ac_count", 0)) >= 3,
        "has_min_gwt": int(score.get("gwt_count", 0)) >= 3,
        "be_ready": bool(score.get("be_ready", score.get("task_groups_ready", False))),
        "fe_ready": bool(score.get("fe_ready", score.get("task_groups_ready", False))),
        "qa_ready": bool(score.get("qa_ready", score.get("task_groups_ready", False))),
        "has_min_dod": int(score.get("dod_count", 0)) >= 4,
        "validator_passed": bool(validation.get("passed")),
        "wrong_domain_or_hallucination": bool(domain_issues),
        "generic_output": _story_has_generic_output(story),
        "non_actionable_task": _story_has_non_actionable_task(story),
        "similar_acceptance_criteria": bool(similar_pairs),
        "evaluator_warning_contradicts_approval": _evaluator_warning_contradicts_approval(result),
        "timeout_or_pipeline_failure": timeout_or_pipeline_failure(result),
        "expected_context_missing": has_expected_sources and not bool(score.get("context_hit")),
        "context_noise": bool(context.get("ignored_context_sources")) and not bool(score.get("context_hit")),
    }


def golden_eligibility(result: dict[str, Any]) -> dict[str, Any]:
    score = result.get("score", {}) if isinstance(result.get("score"), dict) else {}
    score_value = float(score.get("score", 0.0))
    flags = build_classification_flags(result)
    blockers: list[str] = []
    if score_value < 85:
        blockers.append("score_below_85")
    required_flags = {
        "retrieval_ok": "retrieval_status_not_ok",
        "evaluation_approved": "evaluation_not_approved",
        "planning_ready": "planning_status_not_ready",
        "context_hit": "expected_context_missing",
        "has_min_ac": "missing_acceptance_criteria",
        "has_min_gwt": "missing_given_when_then",
        "be_ready": "missing_be",
        "fe_ready": "missing_fe",
        "qa_ready": "missing_qa",
        "has_min_dod": "missing_definition_of_done",
        "validator_passed": "validator_failed",
    }
    blockers.extend(reason for flag, reason in required_flags.items() if not flags[flag])
    if flags["timeout_or_pipeline_failure"]:
        blockers.append("timeout_or_pipeline_failure")
    if flags["wrong_domain_or_hallucination"]:
        blockers.append("domain_contamination")
    if flags["generic_output"]:
        blockers.append("generic_output")
    if flags["non_actionable_task"]:
        blockers.append("non_actionable_task")
    if flags["similar_acceptance_criteria"]:
        blockers.append("similar_acceptance_criteria")
    if flags["evaluator_warning_contradicts_approval"]:
        blockers.append("evaluator_warning_contradicts_approval")
    blockers = list(dict.fromkeys(blockers))
    return {
        "eligible": not blockers,
        "reasons": ["score>=85", "evaluation_approved", "context_hit", "ready_structure_complete", "validator_passed"] if not blockers else [],
        "blockers": blockers,
        "quality": {"score": score_value, "flags": flags},
    }


def classify_benchmark_result(result: dict[str, Any]) -> dict[str, Any]:
    score_value = float(result.get("score", {}).get("score", 0.0)) if isinstance(result.get("score"), dict) else 0.0
    flags = build_classification_flags(result)
    reasons: list[str] = []

    if not flags["retrieval_ok"] or flags["timeout_or_pipeline_failure"] or flags["expected_context_missing"]:
        if not flags["retrieval_ok"]:
            reasons.append("retrieval_status_not_ok")
        if flags["timeout_or_pipeline_failure"]:
            reasons.append("timeout_or_pipeline_failure")
        if flags["expected_context_missing"]:
            reasons.append("expected_context_missing")
        if flags["context_noise"]:
            reasons.append("context_noise")
        return {
            "class": "D",
            "label": "Retrieval or timeout failure",
            "reasons": reasons,
            "flags": flags,
        }

    eligibility = golden_eligibility(result)
    if eligibility["eligible"]:
        return {
            "class": "A",
            "label": "Golden positive",
            "reasons": eligibility["reasons"],
            "flags": flags,
            "golden_eligibility": eligibility,
        }

    hard_output_failure = (
        flags["wrong_domain_or_hallucination"]
        or flags["generic_output"]
        or flags["non_actionable_task"]
        or flags["similar_acceptance_criteria"]
        or flags["evaluator_warning_contradicts_approval"]
        or (score_value >= 85 and not flags["validator_passed"])
    )
    if 70 <= score_value <= 84 and not hard_output_failure:
        polish_reasons = ["score_70_84", "retrieval_ok"]
        if not flags["has_min_ac"] or not flags["has_min_gwt"]:
            polish_reasons.append("acceptance_criteria_needs_polish")
        if not flags["has_min_dod"]:
            polish_reasons.append("definition_of_done_needs_polish")
        if not all((flags["be_ready"], flags["fe_ready"], flags["qa_ready"])):
            polish_reasons.append("task_breakdown_needs_polish")
        return {
            "class": "B",
            "label": "Usable but needs polish",
            "reasons": polish_reasons,
            "flags": flags,
        }

    bad_reasons = ["prompt_or_output_failure"]
    if score_value < 70:
        bad_reasons.append("score_below_70")
    if hard_output_failure:
        bad_reasons.append("wrong_domain_or_generic_output")
    if flags["evaluation_approved"] and eligibility["blockers"]:
        bad_reasons.append("evaluator_false_approve")
    if not flags["has_min_ac"]:
        bad_reasons.append("missing_acceptance_criteria")
    if not flags["qa_ready"]:
        bad_reasons.append("missing_qa")
    return {
        "class": "C",
        "label": "Bad output / prompt failure",
        "reasons": bad_reasons,
        "flags": flags,
    }


def compact_case_for_result(case: dict[str, Any]) -> dict[str, Any]:
    requirement = str(case.get("requirement", ""))
    return {
        "id": case.get("id", requirement[:40]),
        "expected_status": case.get("expected_status", "READY"),
        "expected_sources": list(case.get("expected_sources", [])),
        "requirement": requirement,
    }


def context_for_result(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "retrieval_status": context.get("retrieval_status"),
        "retrieval_threshold": context.get("retrieval_threshold"),
        "raw_match_count": context.get("raw_match_count"),
        "confidence": context.get("confidence"),
        "retrieved_sources": context.get("retrieved_sources", []),
        "selected_context_sources": context.get("selected_context_sources", []),
        "ignored_context_sources": context.get("ignored_context_sources", []),
        "context_snippets": context.get("context_snippets", []),
        "planning_brief": context.get("planning_brief", {}),
        "quality_gate": context.get("quality_gate", {}),
        "warnings": context.get("warnings", []),
        "route": context.get("route", {}),
    }


def elapsed_ms(started_at: float) -> int:
    return max(0, round((time.perf_counter() - started_at) * 1000))


def run_case(version: str, case: dict[str, Any], n_results: int) -> dict[str, Any]:
    started_at = time.perf_counter()
    os.environ["PLANNER_PROMPT_VERSION"] = version
    requirement = case["requirement"]
    route = route_for_benchmark_case(case)
    context = ResearcherAgent().run(
        requirement,
        n_results=n_results,
        route=route,
    )
    story = PlannerAgent().run(
        requirement,
        context,
        requirement_type=route.get("story_type") or "software_feature",
        route=route,
    )
    evaluation = EvaluatorAgent().run(story)
    score = score_story(case, context, story, evaluation)
    case_latency_ms = elapsed_ms(started_at)
    stage_latencies_ms = {
        **(context.get("stage_latencies_ms", {}) if isinstance(context.get("stage_latencies_ms"), dict) else {}),
        **(story.get("stage_latencies_ms", {}) if isinstance(story.get("stage_latencies_ms"), dict) else {}),
        "case_total_ms": case_latency_ms,
    }
    result = {
        "case_id": case.get("id", requirement[:40]),
        "version": version,
        "score": score,
        "retrieval_status": context.get("retrieval_status"),
        "context_sources": [source.get("source") for source in context.get("retrieved_sources", [])],
        "title": story.get("title"),
        "planning_status": story.get("planning_status"),
        "evaluation_status": evaluation.get("status"),
        "evaluation_issues": evaluation.get("issues", []),
        "warnings": story.get("warnings", []),
        "latency_ms": case_latency_ms,
        "stage_latencies_ms": stage_latencies_ms,
        "timed_out": bool(story.get("timed_out")),
        "failure_type": story.get("failure_type", ""),
        "case": compact_case_for_result(case),
        "context": context_for_result(context),
        "story": story,
        "evaluation": evaluation,
    }
    classification = classify_benchmark_result(result)
    result.update(
        {
            "classification": classification["class"],
            "classification_label": classification["label"],
            "classification_reasons": classification["reasons"],
            "classification_flags": classification["flags"],
        }
    )
    return result


def select_golden_samples(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for result in results:
        if result.get("classification") != "A" or not golden_eligibility(result)["eligible"]:
            continue
        case_id = str(result.get("case_id", ""))
        current = selected.get(case_id)
        if current is None or (result["score"]["score"], result.get("version") == "current") > (current["score"]["score"], current.get("version") == "current"):
            selected[case_id] = result
    return [selected[case_id] for case_id in sorted(selected)]


def build_golden_samples_payload(results: list[dict[str, Any]]) -> dict[str, Any]:
    samples = []
    for result in select_golden_samples(results):
        story = result.get("story", {}) if isinstance(result.get("story"), dict) else {}
        context = result.get("context", {}) if isinstance(result.get("context"), dict) else {}
        eligibility = golden_eligibility(result)
        samples.append(
            {
                "id": str(result.get("case_id")),
                "source_case_id": result.get("case_id"),
                "benchmark_version": result.get("version"),
                "requirement": _case_requirement(result, story),
                "story_type": story.get("story_type"),
                "expected_status": result.get("case", {}).get("expected_status", "READY") if isinstance(result.get("case"), dict) else "READY",
                "expected_sources": result.get("case", {}).get("expected_sources", []) if isinstance(result.get("case"), dict) else [],
                "context_sources": context.get("selected_context_sources") or context.get("retrieved_sources", []),
                "story": story,
                "evaluation_status": result.get("evaluation_status"),
                "score": result.get("score", {}).get("score"),
                "classification_reasons": result.get("classification_reasons", []),
                "quality_flags": eligibility["quality"]["flags"],
                "why_golden": eligibility["reasons"],
            }
        )
    return {
        "schema_version": 1,
        "selection_policy": {"classification": "A", "min_score": 85, "requires_validator_passed": True},
        "samples": samples,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def result_title(result: dict[str, Any]) -> Any:
    if result.get("title"):
        return result.get("title")
    story = result.get("story", {}) if isinstance(result.get("story"), dict) else {}
    return story.get("title")


def classification_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(result.get("classification", "unclassified") for result in results)
    case_ids_by_class = {
        class_name: [result["case_id"] for result in results if result.get("classification") == class_name]
        for class_name in ("A", "B", "C", "D")
    }
    reason_counts = Counter(
        reason
        for result in results
        for reason in result.get("classification_reasons", [])
    )
    golden_candidates = sorted(
        [
            {"case_id": result["case_id"], "score": result["score"]["score"], "title": result_title(result)}
            for result in results
            if result.get("classification") == "A"
        ],
        key=lambda item: item["score"],
        reverse=True,
    )
    return {
        "classification_counts": {class_name: counts.get(class_name, 0) for class_name in ("A", "B", "C", "D")},
        "golden_case_ids": case_ids_by_class["A"],
        "usable_case_ids": case_ids_by_class["B"],
        "prompt_failure_case_ids": case_ids_by_class["C"],
        "retrieval_failure_case_ids": case_ids_by_class["D"],
        "golden_candidates": golden_candidates,
        "top_classification_reasons": dict(reason_counts.most_common()),
    }


def build_report(versions: list[str], results: list[dict[str, Any]]) -> dict[str, Any]:
    by_version = {}
    for version in versions:
        version_results = [result for result in results if result["version"] == version]
        by_version[version] = {
            "cases": len(version_results),
            "average_score": round(mean(result["score"]["score"] for result in version_results), 2) if version_results else 0,
            "approved_count": sum(1 for result in version_results if result["evaluation_status"] == "APPROVED"),
            **classification_summary(version_results),
        }
    return {
        "versions": versions,
        "summary": by_version,
        "golden_candidates": [
            {"version": result["version"], "case_id": result["case_id"], "score": result["score"]["score"], "title": result_title(result)}
            for result in sorted(results, key=lambda item: item["score"]["score"], reverse=True)
            if result.get("classification") == "A"
        ],
        "results": results,
    }


def run_benchmark(
    cases_path: Path,
    versions: list[str],
    n_results: int,
    offset: int = 0,
    limit: int = 0,
    output: Path | None = None,
    golden_output: Path | None = None,
) -> dict[str, Any]:
    cases = select_cases(load_cases(cases_path), offset=offset, limit=limit)
    results = []
    for version in versions:
        for index, case in enumerate(cases, start=offset):
            result = run_case(version, case, n_results)
            result["case_index"] = index
            results.append(result)
            if output is not None:
                append_jsonl(output, result)
    report = build_report(versions, results)
    if golden_output is not None:
        write_json(golden_output, build_golden_samples_payload(results))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Planner prompt versions with the same RAG and evaluator pipeline.")
    parser.add_argument("--cases", default="src/ai_scrum_master/data/swe_bench_sample/planner_cases_first50.json")
    parser.add_argument("--versions", nargs="+", default=["current"])
    parser.add_argument("--n-results", type=int, default=3)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--output", default="")
    parser.add_argument("--golden-output", default="")
    args = parser.parse_args()

    report = run_benchmark(
        cases_path=Path(args.cases),
        versions=args.versions,
        n_results=args.n_results,
        offset=args.offset,
        limit=args.limit,
        output=Path(args.output) if args.output else None,
        golden_output=Path(args.golden_output) if args.golden_output else None,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    best_version = max(report["summary"], key=lambda version: report["summary"][version]["average_score"]) if report["summary"] else None
    return 0 if best_version and report["summary"][best_version]["average_score"] >= 80 else 1


if __name__ == "__main__":
    raise SystemExit(main())
