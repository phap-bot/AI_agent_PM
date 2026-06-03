import json

import ai_scrum_master.evaluation.planner_benchmark as planner_benchmark
from ai_scrum_master.evaluation.planner_benchmark import (
    build_report,
    classification_summary,
    classify_benchmark_result,
    build_golden_samples_payload,
    golden_eligibility,
    run_benchmark,
    score_story,
    select_golden_samples,
    timeout_or_pipeline_failure,
)


def make_result(**overrides):
    result = {
        "case_id": "case-1",
        "version": "current",
        "score": {
            "score": 90,
            "context_hit": True,
            "gwt_count": 3,
            "ac_count": 3,
            "task_groups_ready": True,
            "be_ready": True,
            "fe_ready": True,
            "qa_ready": True,
            "dod_count": 4,
        },
        "retrieval_status": "ok",
        "evaluation_status": "APPROVED",
        "evaluation_issues": [],
        "warnings": [],
        "case": {
            "expected_sources": ["auth_context"],
            "requirement": "As a user, I want Google login so that I can sign in faster.",
        },
        "context": {"warnings": [], "retrieved_sources": [{"source": "auth_context"}]},
        "story": {
            "title": "Google Login",
            "requirement": "As a user, I want Google login so that I can sign in faster.",
            "planning_status": "READY",
            "story_type": "software_feature",
            "context_sources": [{"source": "auth_context"}],
            "story_points": 5,
            "acceptance_criteria": [
                "Given Google auth is enabled, when a user clicks login, then Google OAuth starts.",
                "Given Google authentication succeeds, when the callback returns, then the user is signed in.",
                "Given authentication fails, when the provider rejects the request, then the user sees an error message.",
            ],
            "tasks": {
                "be": ["Implement OAuth callback and session handoff"],
                "fe": ["Add Google login button and error state"],
                "qa": ["Validate happy path and failed authentication scenarios"],
            },
            "definition_of_done": ["One", "Two", "Three", "Four"],
        },
        "evaluation": {"warnings": []},
    }
    for key, value in overrides.items():
        if key == "score":
            result["score"] = {**result["score"], **value}
        else:
            result[key] = value
    return result


def with_classification(result):
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


def test_classifies_strict_golden_positive() -> None:
    classification = classify_benchmark_result(make_result())

    assert classification["class"] == "A"
    assert classification["label"] == "Golden positive"
    assert "ready_structure_complete" in classification["reasons"]


def test_golden_eligibility_exposes_quality_contract() -> None:
    eligibility = golden_eligibility(make_result())

    assert eligibility["eligible"] is True
    assert eligibility["blockers"] == []
    assert "validator_passed" in eligibility["reasons"]


def test_retrieval_failure_precedes_high_score_and_approval() -> None:
    classification = classify_benchmark_result(make_result(retrieval_status="no_context"))

    assert classification["class"] == "D"
    assert "retrieval_status_not_ok" in classification["reasons"]


def test_expected_context_missing_is_retrieval_failure() -> None:
    classification = classify_benchmark_result(make_result(score={"context_hit": False}))

    assert classification["class"] == "D"
    assert "expected_context_missing" in classification["reasons"]


def test_classifies_usable_needs_polish_for_score_70_to_84() -> None:
    classification = classify_benchmark_result(
        make_result(
            score={"score": 78, "dod_count": 2, "context_hit": True},
            evaluation_status="REVISION",
        )
    )

    assert classification["class"] == "B"
    assert "definition_of_done_needs_polish" in classification["reasons"]


def test_evaluator_false_approval_missing_qa_is_bad_output() -> None:
    classification = classify_benchmark_result(
        make_result(
            score={"score": 88, "qa_ready": False, "task_groups_ready": False},
        )
    )

    assert classification["class"] == "C"
    assert "evaluator_false_approve" in classification["reasons"]
    assert "missing_qa" in classification["reasons"]


def test_generic_output_is_bad_output_not_polish() -> None:
    result = make_result(score={"score": 75})
    result["story"] = {
        **result["story"],
        "acceptance_criteria": [
            "Given the requirement is approved, when planning starts, then the story is documented clearly.",
            "Given Google authentication succeeds, when the callback returns, then the user is signed in.",
            "Given authentication fails, when the provider rejects the request, then the user sees an error message.",
        ],
    }

    classification = classify_benchmark_result(result)

    assert classification["class"] == "C"
    assert "wrong_domain_or_generic_output" in classification["reasons"]


def test_high_score_wrong_domain_cannot_be_golden() -> None:
    result = make_result()
    result["story"] = {**result["story"], "title": "Sprint Planning Checkout", "user_story": "As a scrum master, I want checkout sprint planning so that the team can plan."}

    classification = classify_benchmark_result(result)

    assert classification["class"] == "C"
    assert "domain_contamination" in golden_eligibility(result)["blockers"]


def test_high_score_placeholder_task_cannot_be_golden() -> None:
    result = make_result()
    result["story"]["tasks"]["be"] = ["Define backend changes"]

    classification = classify_benchmark_result(result)

    assert classification["class"] == "C"
    assert "non_actionable_task" in golden_eligibility(result)["blockers"]


def test_similar_acceptance_criteria_block_golden() -> None:
    result = make_result()
    result["story"]["acceptance_criteria"] = [
        "Given Google login is enabled, when a user clicks the Google login button, then OAuth starts.",
        "Given Google login is enabled, when a user selects the Google login button, then OAuth starts.",
        "Given Google authentication fails, when the provider rejects the request, then the user sees an error message.",
    ]

    classification = classify_benchmark_result(result)

    assert classification["class"] == "C"
    assert "similar_acceptance_criteria" in golden_eligibility(result)["blockers"]


def test_evaluator_warning_contradicting_approval_blocks_golden() -> None:
    result = make_result(evaluation={"warnings": ["Missing QA validation must be fixed."]})

    classification = classify_benchmark_result(result)

    assert classification["class"] == "C"
    assert "evaluator_warning_contradicts_approval" in golden_eligibility(result)["blockers"]


def test_score_story_exposes_task_group_flags() -> None:
    scored = score_story(
        {"expected_sources": ["auth_context"], "expected_status": "READY"},
        {"retrieved_sources": [{"source": "auth_context"}]},
        {
            "planning_status": "READY",
            "acceptance_criteria": [
                "Given one, when two, then three.",
                "Given one, when two, then three.",
                "Given one, when two, then three.",
            ],
            "tasks": {"be": ["Implement backend"], "fe": [], "qa": ["Test flow"]},
            "definition_of_done": ["One", "Two", "Three", "Four"],
        },
        {"status": "APPROVED"},
    )

    assert scored["be_ready"] is True
    assert scored["fe_ready"] is False
    assert scored["qa_ready"] is True
    assert scored["task_groups_ready"] is False


def test_timeout_detection_uses_structured_failure_fields() -> None:
    assert timeout_or_pipeline_failure({"failure_type": "planner_exception"}) is True
    assert timeout_or_pipeline_failure({"story": {"timed_out": True}}) is True
    assert timeout_or_pipeline_failure({"story": {"failure_type": "planner_timeout"}}) is True


def test_classification_summary_groups_case_ids_and_reasons() -> None:
    results = [
        with_classification(make_result(case_id="a")),
        with_classification(make_result(case_id="d", retrieval_status="failed")),
    ]

    summary = classification_summary(results)

    assert summary["classification_counts"] == {"A": 1, "B": 0, "C": 0, "D": 1}
    assert summary["golden_case_ids"] == ["a"]
    assert summary["retrieval_failure_case_ids"] == ["d"]
    assert summary["golden_candidates"] == [{"case_id": "a", "score": 90, "title": "Google Login"}]


def test_build_report_includes_classification_summary_per_version_and_overall_golden_candidates() -> None:
    results = [with_classification(make_result(case_id="a", version="current"))]

    report = build_report(["current"], results)

    assert report["summary"]["current"]["classification_counts"] == {"A": 1, "B": 0, "C": 0, "D": 0}
    assert report["summary"]["current"]["golden_case_ids"] == ["a"]
    assert report["golden_candidates"] == [
        {"version": "current", "case_id": "a", "score": 90, "title": "Google Login"}
    ]


def test_select_golden_samples_only_keeps_strict_a_results() -> None:
    golden = with_classification(make_result(case_id="a"))
    bad = with_classification(make_result(case_id="b", retrieval_status="failed"))
    polish = with_classification(make_result(case_id="c", score={"score": 78}, evaluation_status="REVISION"))

    assert [result["case_id"] for result in select_golden_samples([bad, polish, golden])] == ["a"]


def test_select_golden_samples_deduplicates_by_case_id() -> None:
    older = with_classification(make_result(case_id="a", version="draft", score={"score": 90}))
    current = with_classification(make_result(case_id="a", version="current", score={"score": 90}))
    higher = with_classification(make_result(case_id="b", version="draft", score={"score": 95}))
    lower = with_classification(make_result(case_id="b", version="current", score={"score": 90}))

    selected = select_golden_samples([older, current, lower, higher])

    assert [(result["case_id"], result["version"], result["score"]["score"]) for result in selected] == [("a", "current", 90), ("b", "draft", 95)]


def test_build_golden_samples_payload_schema_and_story_contract() -> None:
    result = with_classification(make_result(case_id="a"))

    payload = build_golden_samples_payload([result])
    sample = payload["samples"][0]

    assert payload["selection_policy"] == {"classification": "A", "min_score": 85, "requires_validator_passed": True}
    assert sample["id"] == "a"
    assert sample["evaluation_status"] == "APPROVED"
    assert sample["quality_flags"]["validator_passed"] is True
    assert sample["story"]["planning_status"] == "READY"
    assert "latency_ms" not in sample


def test_run_benchmark_writes_golden_output(tmp_path, monkeypatch) -> None:
    cases_path = tmp_path / "cases.json"
    golden_output = tmp_path / "goldens.json"
    cases_path.write_text(json.dumps([{"id": "a", "requirement": "Add Google login"}]), encoding="utf-8")
    monkeypatch.setattr(planner_benchmark, "run_case", lambda version, case, n_results: with_classification(make_result(case_id=case["id"], version=version)))

    report = run_benchmark(cases_path, ["current"], n_results=1, golden_output=golden_output)
    payload = json.loads(golden_output.read_text(encoding="utf-8"))

    assert report["summary"]["current"]["golden_case_ids"] == ["a"]
    assert payload["samples"][0]["source_case_id"] == "a"
    assert payload["samples"][0]["quality_flags"]["validator_passed"] is True
