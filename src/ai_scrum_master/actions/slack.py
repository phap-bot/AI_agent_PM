from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_scrum_master.core.config import get_settings
from ai_scrum_master.core.http_client import HttpClient, HttpResponse, UrllibHttpClient
from ai_scrum_master.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class SlackConfig:
    webhook_url: str
    mention_user_id: str = ""

    @property
    def is_configured(self) -> bool:
        return bool(self.webhook_url)


class SlackTool:
    def __init__(self, config: SlackConfig | None = None, http_client: HttpClient | None = None) -> None:
        settings = get_settings()
        self.config = config or SlackConfig(
            webhook_url=settings.slack_webhook_url,
            mention_user_id=settings.slack_mention_user_id
        )
        self.http_client = http_client or UrllibHttpClient()

    def build_story_message(self, story: dict, evaluation: dict, jira_created: dict[str, Any] | None = None) -> dict[str, Any]:
        jira_text = "Draft (Not created yet)"
        if jira_created and jira_created.get("story_key"):
            story_url = jira_created.get("story", {}).get("url", "")
            jira_text = f"<{story_url}|{jira_created['story_key']}>" if story_url else jira_created['story_key']

        subtasks_text = ""
        tasks = story.get("tasks", {})
        if isinstance(tasks, dict):
            for group, task_list in tasks.items():
                for task in task_list:
                    subtasks_text += f"• {group.upper()} - {task}\n"
        
        if not subtasks_text.strip():
            subtasks_text = "No subtasks"

        mention_text = f"<@{self.config.mention_user_id}> " if self.config.mention_user_id else ""

        return {
            "text": f"AI Scrum Master created a Jira story: {story.get('title')}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{mention_text}*AI Scrum Master created a Jira story*\n\n"
                                f"*Story:* {story.get('title')}\n"
                                f"*Jira:* {jira_text}\n"
                                f"*Priority:* High\n"
                                f"*Story Points:* {story.get('story_points')}\n"
                                f"*Status:* To Do"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Subtasks:*\n{subtasks_text.strip()}"
                    }
                }
            ]
        }

    def prepare_action(self, story: dict, evaluation: dict, jira_created: dict[str, Any] | None = None) -> dict[str, Any]:
        message = self.build_story_message(story, evaluation, jira_created)
        if not self.config.is_configured:
            return {
                "ready": False,
                "payload": message,
                "warnings": ["Slack is not configured; set SLACK_WEBHOOK_URL."],
            }

        return {
            "ready": True,
            "payload": message,
            "warnings": [],
        }

    def execute_action(self, story: dict, evaluation: dict, jira_created: dict[str, Any] | None = None) -> dict[str, Any]:
        message = self.build_story_message(story, evaluation, jira_created)
        if not self.config.is_configured:
            logger.info("Slack execution skipped because webhook is missing")
            return {
                "ready": False,
                "executed": False,
                "payload": message,
                "created": {},
                "failed": [],
                "warnings": ["Slack is not configured; set SLACK_WEBHOOK_URL."],
                "status_code": None,
            }

        logger.info("Slack notification send started")
        response = self._post_with_retry(message)
        executed = 200 <= response.status_code < 300
        logger.info("Slack notification send completed status_code=%s executed=%s", response.status_code, executed)
        return {
            "ready": True,
            "executed": executed,
            "payload": message,
            "created": {"message": "sent"} if executed else {},
            "failed": [] if executed else [{"status_code": response.status_code, "text": response.text}],
            "warnings": self._warnings_for_response(response),
            "status_code": response.status_code,
        }

    def _post_with_retry(self, payload: dict[str, Any]) -> HttpResponse:
        response = HttpResponse(status_code=0, text="No request attempted")
        for attempt in range(1, 4):
            response = self.http_client.post_json(url=self.config.webhook_url, payload=payload)
            if response.status_code not in {0, 429} and response.status_code < 500:
                return response
            logger.info("Slack request retryable status_code=%s attempt=%s", response.status_code, attempt)
        return response

    def _warnings_for_response(self, response: HttpResponse) -> list[str]:
        if 200 <= response.status_code < 300:
            return []
        if response.status_code == 429:
            return ["Slack rate limit persisted after retries."]
        if response.status_code >= 500:
            return ["Slack server error persisted after retries."]
        if response.status_code == 0:
            return [f"Slack request failed before receiving a response: {response.text}"]
        return [f"Slack request failed with status {response.status_code}."]
