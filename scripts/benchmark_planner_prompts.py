from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from statistics import mean
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ai_scrum_master.agents.evaluator import EvaluatorAgent
from ai_scrum_master.agents.planner import PlannerAgent
from ai_scrum_master.agents.researcher import ResearcherAgent
from ai_scrum_master.core.quality import classify_requirement


def load_cases(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def score_story(case: dict[str, Any], context: dict[str, Any], story: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
    criteria = story.get("acceptance_criteria", [])
    tasks = story.get("tasks", {}) if isinstance(story.get("tasks"), dict) else {}
    dod = story.get("definition_of_done", [])
    expected_sources = set(case.get("expected_sources", []))
    actual_sources = {source.get("source") for source in context.get("retrieved_sources", []) if isinstance(source, dict)}
    context_hit = bool(expected_sources & actual_sources) if expected_sources else bool(actual_sources)
    task_groups_ready = all(isinstance(tasks.get(group), list) and tasks.get(group) for group in ("be", "fe", "qa"))
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
        "dod_count": len(dod),
    }


def run_case(version: str, case: dict[str, Any], n_results: int) -> dict[str, Any]:
    os.environ["PLANNER_PROMPT_VERSION"] = version
    requirement = case["requirement"]
    context = ResearcherAgent().run(requirement, n_results=n_results)
    story = PlannerAgent().run(
        requirement,
        context,
        requirement_type=classify_requirement(requirement),
    )
    evaluation = EvaluatorAgent().run(story)
    score = score_story(case, context, story, evaluation)
    return {
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
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Planner prompt versions with the same RAG and evaluator pipeline.")
    parser.add_argument("--cases", default="data/planner_benchmark_cases.json")
    parser.add_argument("--versions", nargs="+", default=["v1", "v2"])
    parser.add_argument("--n-results", type=int, default=5)
    args = parser.parse_args()

    cases = load_cases(Path(args.cases))
    results = []
    for version in args.versions:
        for case in cases:
            results.append(run_case(version, case, args.n_results))

    by_version = {}
    for version in args.versions:
        version_results = [result for result in results if result["version"] == version]
        by_version[version] = {
            "cases": len(version_results),
            "average_score": round(mean(result["score"]["score"] for result in version_results), 2) if version_results else 0,
            "approved_count": sum(1 for result in version_results if result["evaluation_status"] == "APPROVED"),
        }

    report = {
        "versions": args.versions,
        "summary": by_version,
        "results": results,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    best_version = max(by_version, key=lambda version: by_version[version]["average_score"]) if by_version else None
    return 0 if best_version and by_version[best_version]["average_score"] >= 80 else 1


if __name__ == "__main__":
    raise SystemExit(main())
