import json

import pytest
from pydantic import ValidationError

from ai_scrum_master.agents.evaluator import EvaluatorAgent
from ai_scrum_master.agents.planner import PlannerAgent
from ai_scrum_master.api.schemas import GenerateStoriesResponse, StoryDraft, sanitize_markdown
from ai_scrum_master.core.agent_schemas import EvaluationOutput, PlannerStoryOutput
from ai_scrum_master.core.llm_json import normalize_llm_json_output


VALID_STORY_PAYLOAD = {
    "title": "Fix BlackBody scale validation",
    "user_story": "As a maintainer, I want BlackBody scale validation so that invalid units fail clearly.",
    "acceptance_criteria": [
        "Given invalid scale units, when BlackBody validates input, then a clear error is raised.",
        "Given dimensionless scale, when BlackBody evaluates flux, then the existing behavior remains supported.",
        "Given regression tests run, when the fix is applied, then the bolometric flux behavior is covered.",
    ],
    "story_points": 8,
    "tasks": {
        "be": ["Implement strict scale unit validation in BlackBody evaluation."],
        "fe": ["Document user-facing error behavior for invalid scale units."],
        "qa": ["Add regression tests for invalid and dimensionless scale values."],
    },
    "definition_of_done": [
        "Acceptance criteria are validated with regression tests.",
        "Backend implementation is reviewed and complete.",
        "QA evidence covers invalid scale and dimensionless scale behavior.",
        "Documentation or release note impact is reviewed.",
    ],
    "planning_status": "READY",
}


def test_normalize_llm_json_strips_backtick_fence() -> None:
    text = "```json\n{\"status\": \"APPROVED\"}\n```"

    assert json.loads(normalize_llm_json_output(text)) == {"status": "APPROVED"}


def test_normalize_llm_json_strips_single_quote_fence() -> None:
    text = "'''json\n{\"status\": \"REVISION\"}\n'''"

    assert json.loads(normalize_llm_json_output(text)) == {"status": "REVISION"}


def test_normalize_llm_json_extracts_object_from_conversation() -> None:
    text = "Sure, here is the JSON you requested:\n{\"status\": \"APPROVED\", \"issues\": []}\nDone."

    assert json.loads(normalize_llm_json_output(text))["status"] == "APPROVED"


def test_normalize_llm_json_rejects_non_json_text() -> None:
    with pytest.raises(ValueError):
        normalize_llm_json_output("Sure, I can help, but no object here.")


def test_planner_parse_story_accepts_fenced_json() -> None:
    raw = "```json\n" + json.dumps(VALID_STORY_PAYLOAD) + "\n```"

    parsed = PlannerAgent(use_llm=False)._parse_story(raw)

    assert parsed["title"] == "Fix BlackBody scale validation"
    assert parsed["story_points"] == 8


def test_evaluator_parse_result_accepts_single_quote_fenced_json() -> None:
    raw = "'''json\n{\"status\": \"APPROVED\", \"issues\": []}\n'''"

    parsed = EvaluatorAgent(use_llm=False)._parse_result(raw)

    assert parsed == {"status": "APPROVED", "issues": []}


def test_planner_story_output_uses_safe_defaults_for_missing_fields() -> None:
    story = PlannerStoryOutput.model_validate({})

    assert story.title == ""
    assert story.user_story == ""
    assert story.acceptance_criteria == []
    assert story.tasks.be == []
    assert story.definition_of_done == []
    assert story.planning_status == "REVISION"


def test_evaluation_output_defaults_to_revision_when_status_missing() -> None:
    evaluation = EvaluationOutput.model_validate({})

    assert evaluation.status == "REVISION"
    assert evaluation.issues == []


def test_story_points_accept_strict_integer() -> None:
    story = PlannerStoryOutput.model_validate({**VALID_STORY_PAYLOAD, "story_points": 8})

    assert story.story_points == 8


@pytest.mark.parametrize("bad_value", ["8", "tám"])
def test_story_points_reject_string_values(bad_value: str) -> None:
    with pytest.raises(ValidationError):
        PlannerStoryOutput.model_validate({**VALID_STORY_PAYLOAD, "story_points": bad_value})


def test_api_story_draft_defaults_for_ui_survival() -> None:
    draft = StoryDraft.model_validate({})

    assert draft.title == ""
    assert draft.user_story == ""
    assert draft.acceptance_criteria == []
    assert draft.tasks == {"be": [], "fe": [], "qa": []}
    assert draft.definition_of_done == []


def test_api_response_defaults_for_react_survival() -> None:
    response = GenerateStoriesResponse.model_validate({})

    assert response.context.documents == []
    assert response.evaluation.status == "REVISION"
    assert response.actions.jira.ready is False
    assert response.actions.slack.ready is False
    assert response.next_steps == []


def test_api_sanitizes_markdown_from_nested_story_fields() -> None:
    draft = StoryDraft.model_validate(
        {
            "title": "```json\n**Google Login**\n```",
            "acceptance_criteria": ["- Given **OAuth** works, when user logs in, then [account](https://example.com) opens."],
            "tasks": {"be": ["`Implement` <b>callback</b>"], "fe": [], "qa": []},
        }
    )

    assert draft.title == "Google Login"
    assert draft.acceptance_criteria == ["- Given OAuth works, when user logs in, then account opens."]
    assert draft.tasks["be"] == ["Implement callback"]


def test_sanitize_markdown_removes_fences_links_and_inline_formatting() -> None:
    assert sanitize_markdown("'''json\n**Hello** [PM](https://example.com)\n'''") == "Hello PM"


def test_sanitize_markdown_preserves_technical_identifiers_with_underscores() -> None:
    assert sanitize_markdown("ai_scrum_master_context") == "ai_scrum_master_context"
    assert sanitize_markdown("auth_context.md#chunk_1") == "auth_context.md#chunk_1"


def test_api_story_draft_rejects_string_story_points() -> None:
    with pytest.raises(ValidationError):
        StoryDraft.model_validate({"story_points": "8"})
