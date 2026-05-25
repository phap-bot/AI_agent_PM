from pathlib import Path

from ai_scrum_master.agents.tools.jira_tool import JiraConfig, JiraTool
from ai_scrum_master.agents.tools.slack_tool import SlackConfig, SlackTool
from ai_scrum_master.api.main import (
    execute_all_actions,
    execute_jira_action,
    execute_slack_action,
    generate_stories,
    health,
    ingest_documents,
    preview_jira_action,
    preview_slack_action,
)
from ai_scrum_master.api.schemas import ActionPreviewRequest, GenerateStoriesRequest, IngestRequest


STORY = {
    "title": "Google Login",
    "user_story": "As a user, I want Google login so that I can sign in faster.",
    "acceptance_criteria": [
        "Given Google auth is enabled, when a user clicks login, then Google OAuth starts.",
        "Given Google authentication succeeds, when the callback returns, then the user is signed in.",
        "Given authentication fails, when the provider rejects the request, then the user sees an error message.",
    ],
    "story_points": 3,
    "tasks": {"be": ["OAuth callback"], "fe": ["Login button"], "qa": ["Auth tests"]},
    "definition_of_done": ["Acceptance criteria pass."],
    "planning_status": "READY",
    "warnings": [],
}

SPLIT_STORY = {
    **STORY,
    "planning_status": "SPLIT_RECOMMENDED",
    "story_splits": [{"title": "Foundation and access"}],
    "sprint_allocation": [{"sprint": 1, "stories": ["Foundation and access"]}],
}


class FakeCrew:
    def run(self, requirement: str, n_results: int = 5) -> dict:
        return {
            "context": {"documents": ["auth uses JWT"], "ids": ["doc-1"], "warnings": []},
            "story": STORY,
            "evaluation": {"status": "APPROVED", "issues": [], "revision_instructions": [], "warnings": []},
            "actions": {
                "jira": {"ready": False, "payload": {"fields": {"summary": STORY["title"]}}, "warnings": ["not configured"]},
                "slack": {"ready": False, "payload": {"text": STORY["title"]}, "warnings": ["not configured"]},
            },
        }


def fake_ingest_runner(raw_docs_dir=None, collection_name=None) -> dict:
    return {
        "collection": collection_name or "project_context",
        "source_dir": str(raw_docs_dir or "data/raw_docs"),
        "files_indexed": 1,
        "chunks_indexed": 1,
    }


def configured_jira_tool() -> JiraTool:
    return JiraTool(
        JiraConfig(
            base_url="https://example.atlassian.net",
            project_key="SCRUM",
            email="pm@example.com",
            api_token="token",
        )
    )


def configured_slack_tool() -> SlackTool:
    return SlackTool(SlackConfig(webhook_url="https://hooks.slack.example"))


class FakeExecutingJiraTool:
    def __init__(self) -> None:
        self.called = False

    def execute_action(self, story: dict) -> dict:
        self.called = True
        return {
            "ready": True,
            "executed": True,
            "payload": {"fields": {"summary": story["title"]}},
            "created": {"story_key": "SCRUM-1", "subtasks": []},
            "failed": [],
            "warnings": [],
            "status_code": 201,
        }


class FakeExecutingSlackTool:
    def __init__(self) -> None:
        self.called = False

    def execute_action(self, story: dict, evaluation: dict) -> dict:
        self.called = True
        return {
            "ready": True,
            "executed": True,
            "payload": {"text": story["title"]},
            "created": {"message": "sent"},
            "failed": [],
            "warnings": [],
            "status_code": 200,
        }


def test_health_endpoint() -> None:
    assert health() == {"status": "ok"}


def test_generate_endpoint_returns_action_plan() -> None:
    response = generate_stories(GenerateStoriesRequest(requirement="Add Google login"), crew=FakeCrew())
    body = response.model_dump()

    assert body["story"]["title"] == "Google Login"
    assert body["evaluation"]["status"] == "APPROVED"
    assert "jira" in body["actions"]
    assert "slack" in body["actions"]


def test_ingest_endpoint_indexes_temp_docs(tmp_path: Path) -> None:
    raw_docs = tmp_path / "raw_docs"
    raw_docs.mkdir()
    (raw_docs / "auth.md").write_text("Auth stack uses JWT and Google OAuth.", encoding="utf-8")

    response = ingest_documents(
        IngestRequest(raw_docs_dir=str(raw_docs), collection_name="api_test_context"),
        ingest_runner=fake_ingest_runner,
    )
    body = response.model_dump()

    assert body["collection"] == "api_test_context"
    assert body["files_indexed"] == 1
    assert body["chunks_indexed"] == 1


def test_jira_preview_endpoint() -> None:
    response = preview_jira_action(
        ActionPreviewRequest(story=STORY, evaluation={"status": "APPROVED"}),
        jira_tool=configured_jira_tool(),
    )
    body = response.model_dump()

    assert body["jira"]["ready"] is True
    assert body["jira"]["payload"]["fields"]["summary"] == "Google Login"


def test_slack_preview_endpoint() -> None:
    response = preview_slack_action(
        ActionPreviewRequest(story=STORY, evaluation={"status": "APPROVED"}),
        slack_tool=configured_slack_tool(),
    )
    body = response.model_dump()

    assert body["slack"]["ready"] is True
    assert body["slack"]["payload"]["text"] == "AI Scrum Master prepared story: Google Login"


def test_jira_preview_blocks_non_ready_planning_status() -> None:
    response = preview_jira_action(
        ActionPreviewRequest(story=SPLIT_STORY, evaluation={"status": "APPROVED"}),
        jira_tool=configured_jira_tool(),
    )
    body = response.model_dump()

    assert body["jira"]["ready"] is False
    assert "planning_status is READY" in body["jira"]["warnings"][0]


def test_jira_execute_blocks_non_ready_planning_status() -> None:
    tool = FakeExecutingJiraTool()
    response = execute_jira_action(
        ActionPreviewRequest(story=SPLIT_STORY, evaluation={"status": "APPROVED"}),
        jira_tool=tool,
    )
    body = response.model_dump()

    assert body["jira"]["executed"] is False
    assert tool.called is False


def test_execute_all_blocks_non_ready_planning_status() -> None:
    jira_tool = FakeExecutingJiraTool()
    slack_tool = FakeExecutingSlackTool()
    response = execute_all_actions(
        ActionPreviewRequest(story=SPLIT_STORY, evaluation={"status": "APPROVED"}),
        jira_tool=jira_tool,
        slack_tool=slack_tool,
    )
    body = response.model_dump()

    assert body["jira"]["executed"] is False
    assert body["slack"]["executed"] is False
    assert jira_tool.called is False
    assert slack_tool.called is False


def test_jira_execute_blocks_revision() -> None:
    tool = FakeExecutingJiraTool()
    response = execute_jira_action(
        ActionPreviewRequest(story=STORY, evaluation={"status": "REVISION"}),
        jira_tool=tool,
    )
    body = response.model_dump()

    assert body["jira"]["executed"] is False
    assert tool.called is False


def test_slack_execute_blocks_revision() -> None:
    tool = FakeExecutingSlackTool()
    response = execute_slack_action(
        ActionPreviewRequest(story=STORY, evaluation={"status": "REVISION"}),
        slack_tool=tool,
    )
    body = response.model_dump()

    assert body["slack"]["executed"] is False
    assert tool.called is False


def test_jira_execute_approved_calls_tool() -> None:
    tool = FakeExecutingJiraTool()
    response = execute_jira_action(
        ActionPreviewRequest(story=STORY, evaluation={"status": "APPROVED"}),
        jira_tool=tool,
    )
    body = response.model_dump()

    assert body["jira"]["executed"] is True
    assert body["jira"]["created"]["story_key"] == "SCRUM-1"
    assert tool.called is True


def test_slack_execute_approved_calls_tool() -> None:
    tool = FakeExecutingSlackTool()
    response = execute_slack_action(
        ActionPreviewRequest(story=STORY, evaluation={"status": "APPROVED"}),
        slack_tool=tool,
    )
    body = response.model_dump()

    assert body["slack"]["executed"] is True
    assert body["slack"]["created"]["message"] == "sent"
    assert tool.called is True


def test_execute_all_returns_both_results() -> None:
    jira_tool = FakeExecutingJiraTool()
    slack_tool = FakeExecutingSlackTool()
    response = execute_all_actions(
        ActionPreviewRequest(story=STORY, evaluation={"status": "APPROVED"}),
        jira_tool=jira_tool,
        slack_tool=slack_tool,
    )
    body = response.model_dump()

    assert body["jira"]["executed"] is True
    assert body["slack"]["executed"] is True
    assert jira_tool.called is True
    assert slack_tool.called is True
