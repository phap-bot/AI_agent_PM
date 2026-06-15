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
    dev_channel_id: str = ""
    qa_channel_id: str = ""

    @property
    def is_configured(self) -> bool:
        return bool(self.webhook_url)


class SlackTool:
    def __init__(self, config: SlackConfig | None = None, http_client: HttpClient | None = None) -> None:
        settings = get_settings()
        self.config = config or SlackConfig(
            webhook_url=settings.slack_webhook_url,
            mention_user_id=settings.slack_mention_user_id,
            dev_channel_id=settings.slack_dev_channel_id,
            qa_channel_id=settings.slack_qa_channel_id
        )
        self.http_client = http_client or UrllibHttpClient()

    @classmethod
    def from_project(cls, project_id: str | None, http_client: HttpClient | None = None) -> SlackTool:
        if not project_id:
            return cls(http_client=http_client)
            
        from ai_scrum_master.core.database import DatabaseManager
        project = DatabaseManager.get_project(project_id)
        if not project or not project.get("slack_config"):
            return cls(http_client=http_client)
            
        db_config = project["slack_config"]
        # Fallback fields from .env if empty in DB
        settings = get_settings()
        config = SlackConfig(
            webhook_url=db_config.get("webhook_url") or settings.slack_webhook_url,
            mention_user_id=db_config.get("mention_user_id") or settings.slack_mention_user_id,
            dev_channel_id=db_config.get("dev_channel_id") or settings.slack_dev_channel_id,
            qa_channel_id=db_config.get("qa_channel_id") or settings.slack_qa_channel_id,
        )
        return cls(config=config, http_client=http_client)

    def build_story_message(self, story: dict, evaluation: dict, jira_created: dict[str, Any] | None = None) -> dict[str, Any]:
        jira_text = "Draft (Not created yet)"
        if jira_created and jira_created.get("story_key"):
            story_url = jira_created.get("story", {}).get("url", "")
            jira_text = f"<{story_url}|{jira_created['story_key']}>" if story_url else jira_created['story_key']

        subtasks_text = ""
        tasks = story.get("tasks", {})
        if isinstance(tasks, dict):
            for group, task_list in tasks.items():
                group_name = group.upper()
                channel_link = ""
                if group in ("be", "fe") and self.config.dev_channel_id:
                    channel_link = f" (👈 <#{self.config.dev_channel_id}>)"
                elif group == "qa" and self.config.qa_channel_id:
                    channel_link = f" (👈 <#{self.config.qa_channel_id}>)"

                if task_list:
                    subtasks_text += f"• *{group_name}*{channel_link}\n"
                    for task in task_list:
                        subtasks_text += f"  - {task}\n"
        
        if not subtasks_text.strip():
            subtasks_text = "No subtasks"

        mention_text = ""
        if self.config.mention_user_id:
            mentions = []
            for uid in self.config.mention_user_id.split(","):
                uid = uid.strip()
                if uid.startswith("!"):
                    mentions.append(f"<{uid}>")
                elif uid.startswith("S"):
                    mentions.append(f"<!subteam^{uid}>")
                else:
                    mentions.append(f"<@{uid}>")
            mention_text = " ".join(mentions) + " "

        priority_val = story.get("priority") or "Medium"
        if "high" in priority_val.lower():
            priority_str = f"{priority_val} 🔴"
        elif "medium" in priority_val.lower():
            priority_str = f"{priority_val} 🟠"
        elif "low" in priority_val.lower():
            priority_str = f"{priority_val} 🟢"
        else:
            priority_str = f"{priority_val} ⚪"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚀 New Jira Story Created",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<!channel> {mention_text}*Story:* {story.get('title')}\n*Jira:* {jira_text}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Priority:*\n{priority_str}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Story Points:*\n{story.get('story_points')} 🎯"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Status:*\nTo Do 📋"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Type:*\nStory 📘"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Subtasks:*\n{subtasks_text.strip()}"
                }
            }
        ]

        return {
            "text": f"AI Scrum Master created a Jira story: {story.get('title')}",
            "blocks": blocks
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
        import time
        response = HttpResponse(status_code=0, text="No request attempted")
        max_attempts = 4
        base_delay = 1.0
        
        for attempt in range(1, max_attempts + 1):
            response = self.http_client.post_json(url=self.config.webhook_url, payload=payload)
            if response.status_code not in {0, 429} and response.status_code < 500:
                return response
                
            if attempt < max_attempts:
                delay = base_delay * (2 ** (attempt - 1))
                logger.info("Slack request retryable status_code=%s attempt=%s, sleeping %.1fs", response.status_code, attempt, delay)
                time.sleep(delay)
            else:
                logger.warning("Slack request failed after max attempts status_code=%s", response.status_code)
                
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
