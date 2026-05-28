from ai_scrum_master.actions.jira import JiraConfig, JiraTool
from ai_scrum_master.actions.slack import SlackConfig, SlackTool


def test_action_tools_live_outside_agents_package() -> None:
    assert JiraConfig(base_url="", project_key="", email="", api_token="").is_configured is False
    assert JiraTool.__module__ == "ai_scrum_master.actions.jira"
    assert SlackConfig(webhook_url="").is_configured is False
    assert SlackTool.__module__ == "ai_scrum_master.actions.slack"
