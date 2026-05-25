from ai_scrum_master.agents.tools.jira_tool import JiraConfig, JiraTool
from ai_scrum_master.agents.tools.slack_tool import SlackConfig, SlackTool
from ai_scrum_master.core.http_client import HttpResponse


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
}


class FakeHttpClient:
    def __init__(self, responses: list[HttpResponse]) -> None:
        self.responses = responses
        self.calls: list[dict] = []

    def get_json(self, **kwargs) -> HttpResponse:
        self.calls.append(kwargs)
        return self.responses.pop(0)

    def post_json(self, **kwargs) -> HttpResponse:
        self.calls.append(kwargs)
        return self.responses.pop(0)


def configured_jira(http_client: FakeHttpClient | None = None) -> JiraTool:
    return JiraTool(
        JiraConfig(
            base_url="https://example.atlassian.net",
            project_key="SCRUM",
            email="pm@example.com",
            api_token="token",
        ),
        http_client=http_client,
    )


def configured_slack(http_client: FakeHttpClient | None = None) -> SlackTool:
    return SlackTool(SlackConfig(webhook_url="https://hooks.slack.example"), http_client=http_client)


def test_jira_story_payload_builder() -> None:
    tool = JiraTool(
        JiraConfig(
            base_url="https://example.atlassian.net",
            project_key="SCRUM",
            email="pm@example.com",
            api_token="token",
        )
    )

    payload = tool.build_story_payload(STORY)

    assert payload["fields"]["project"]["key"] == "SCRUM"
    assert payload["fields"]["summary"] == "Google Login"
    assert payload["fields"]["issuetype"]["name"] == "Story"


def test_jira_prepare_action_warns_when_unconfigured() -> None:
    tool = JiraTool(JiraConfig(base_url="", project_key="", email="", api_token=""))

    action = tool.prepare_action(STORY)

    assert action["ready"] is False
    assert action["payload"]
    assert action["warnings"]


def test_jira_check_auth_returns_safe_account_summary() -> None:
    http = FakeHttpClient(
        [
            HttpResponse(
                status_code=200,
                json_body={
                    "accountId": "abc123",
                    "displayName": "PM User",
                    "emailAddress": "pm@example.com",
                    "extra": "ignored",
                },
            )
        ]
    )
    result = configured_jira(http).check_auth()

    assert result["authenticated"] is True
    assert result["account"] == {
        "account_id": "abc123",
        "display_name": "PM User",
        "email_address": "pm@example.com",
    }
    assert len(http.calls) == 1


def test_slack_message_builder() -> None:
    tool = SlackTool(SlackConfig(webhook_url="https://hooks.slack.example"))

    payload = tool.build_story_message(STORY, {"status": "APPROVED"})

    assert payload["text"] == "AI Scrum Master prepared story: Google Login"
    assert payload["blocks"]


def test_slack_prepare_action_warns_when_unconfigured() -> None:
    tool = SlackTool(SlackConfig(webhook_url=""))

    action = tool.prepare_action(STORY, {"status": "APPROVED"})

    assert action["ready"] is False
    assert action["payload"]
    assert action["warnings"]


def test_jira_execute_warns_when_unconfigured_without_http_call() -> None:
    http = FakeHttpClient([HttpResponse(status_code=201, json_body={"key": "SCRUM-1"})])
    tool = JiraTool(JiraConfig(base_url="", project_key="", email="", api_token=""), http_client=http)

    result = tool.execute_action(STORY)

    assert result["ready"] is False
    assert result["executed"] is False
    assert http.calls == []


def test_jira_execute_creates_story_and_subtasks() -> None:
    http = FakeHttpClient(
        [
            HttpResponse(status_code=201, json_body={"key": "SCRUM-1"}),
            HttpResponse(status_code=201, json_body={"key": "SCRUM-2"}),
            HttpResponse(status_code=201, json_body={"key": "SCRUM-3"}),
            HttpResponse(status_code=201, json_body={"key": "SCRUM-4"}),
        ]
    )
    tool = configured_jira(http)

    result = tool.execute_action(STORY)

    assert result["executed"] is True
    assert result["created"]["story_key"] == "SCRUM-1"
    assert len(result["created"]["subtasks"]) == 3
    assert len(http.calls) == 4


def test_jira_execute_reports_partial_subtask_failure() -> None:
    http = FakeHttpClient(
        [
            HttpResponse(status_code=201, json_body={"key": "SCRUM-1"}),
            HttpResponse(status_code=201, json_body={"key": "SCRUM-2"}),
            HttpResponse(status_code=400, json_body={"error": "bad subtask"}),
            HttpResponse(status_code=201, json_body={"key": "SCRUM-4"}),
        ]
    )
    tool = configured_jira(http)

    result = tool.execute_action(STORY)

    assert result["executed"] is False
    assert result["created"]["story_key"] == "SCRUM-1"
    assert len(result["failed"]) == 1


def test_jira_execute_retries_unauthorized_then_warns() -> None:
    http = FakeHttpClient(
        [
            HttpResponse(status_code=401, text="unauthorized"),
            HttpResponse(status_code=401, text="unauthorized"),
            HttpResponse(status_code=401, text="unauthorized"),
        ]
    )
    tool = configured_jira(http)

    result = tool.execute_action(STORY)

    assert result["executed"] is False
    assert len(http.calls) == 3
    assert any("authorization failed" in warning.lower() for warning in result["warnings"])


def test_jira_execute_retries_transient_failure_then_succeeds() -> None:
    http = FakeHttpClient(
        [
            HttpResponse(status_code=500, text="server error"),
            HttpResponse(status_code=201, json_body={"key": "SCRUM-1"}),
            HttpResponse(status_code=201, json_body={"key": "SCRUM-2"}),
            HttpResponse(status_code=201, json_body={"key": "SCRUM-3"}),
            HttpResponse(status_code=201, json_body={"key": "SCRUM-4"}),
        ]
    )
    tool = configured_jira(http)

    result = tool.execute_action(STORY)

    assert result["executed"] is True
    assert result["created"]["story_key"] == "SCRUM-1"
    assert len(http.calls) == 5


def test_slack_execute_warns_when_unconfigured_without_http_call() -> None:
    http = FakeHttpClient([HttpResponse(status_code=200, text="ok")])
    tool = SlackTool(SlackConfig(webhook_url=""), http_client=http)

    result = tool.execute_action(STORY, {"status": "APPROVED"})

    assert result["ready"] is False
    assert result["executed"] is False
    assert http.calls == []


def test_slack_execute_success() -> None:
    http = FakeHttpClient([HttpResponse(status_code=200, text="ok")])
    tool = configured_slack(http)

    result = tool.execute_action(STORY, {"status": "APPROVED"})

    assert result["executed"] is True
    assert result["status_code"] == 200


def test_slack_execute_retries_transient_failure_then_succeeds() -> None:
    http = FakeHttpClient(
        [
            HttpResponse(status_code=500, text="server error"),
            HttpResponse(status_code=200, text="ok"),
        ]
    )
    tool = configured_slack(http)

    result = tool.execute_action(STORY, {"status": "APPROVED"})

    assert result["executed"] is True
    assert len(http.calls) == 2


def test_slack_execute_permanent_failure_returns_warning() -> None:
    http = FakeHttpClient(
        [
            HttpResponse(status_code=500, text="server error"),
            HttpResponse(status_code=500, text="server error"),
            HttpResponse(status_code=500, text="server error"),
        ]
    )
    tool = configured_slack(http)

    result = tool.execute_action(STORY, {"status": "APPROVED"})

    assert result["executed"] is False
    assert len(http.calls) == 3
    assert result["warnings"]
