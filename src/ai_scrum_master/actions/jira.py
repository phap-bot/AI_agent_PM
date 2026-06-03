from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_scrum_master.core.config import get_settings
from ai_scrum_master.core.http_client import HttpClient, HttpResponse, UrllibHttpClient
from ai_scrum_master.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class JiraConfig:
    base_url: str
    project_key: str
    email: str
    api_token: str
    issue_type: str = "Task"
    subtask_issue_type: str = "Sub-task"

    @property
    def is_configured(self) -> bool:
        return all([self.base_url, self.project_key, self.email, self.api_token])


class JiraTool:
    def __init__(self, config: JiraConfig | None = None, http_client: HttpClient | None = None) -> None:
        settings = get_settings()
        self.config = config or JiraConfig(
            base_url=settings.jira_base_url,
            project_key=settings.jira_project_key,
            email=settings.jira_email,
            api_token=settings.jira_api_token,
            issue_type=settings.jira_issue_type,
            subtask_issue_type=settings.jira_subtask_issue_type,
        )
        self.http_client = http_client or UrllibHttpClient()

    def build_story_payload(self, story: dict) -> dict[str, Any]:
        return {
            "fields": {
                "project": {"key": self.config.project_key},
                "summary": story["title"],
                "description": self._build_adf_description(story),
                "issuetype": {"name": self.config.issue_type},
                "labels": ["ai-scrum-master"],
            }
        }

    def build_subtask_payloads(self, parent_key: str, story: dict) -> list[dict[str, Any]]:
        payloads: list[dict[str, Any]] = []
        for group, tasks in story.get("tasks", {}).items():
            for index, task in enumerate(tasks, start=1):
                payloads.append(
                    {
                        "fields": {
                            "project": {"key": self.config.project_key},
                            "parent": {"key": parent_key},
                            "summary": f"[{group.upper()}-{index:03d}] {task}",
                            "description": self._build_text_adf(f"Task group: {group.upper()}"),
                            "issuetype": {"name": self.config.subtask_issue_type},
                            "labels": ["ai-scrum-master", group.lower()],
                        }
                    }
                )
        return payloads

    def prepare_action(self, story: dict) -> dict[str, Any]:
        payload = self.build_story_payload(story)
        if not self.config.is_configured:
            return {
                "ready": False,
                "payload": payload,
                "subtasks": [],
                "warnings": ["Jira is not configured; set JIRA_BASE_URL, JIRA_PROJECT_KEY, JIRA_EMAIL, and JIRA_API_TOKEN."],
            }

        return {
            "ready": True,
            "payload": payload,
            "subtasks": "Build after story issue key is created.",
            "warnings": [],
        }

    def check_auth(self) -> dict[str, Any]:
        if not self.config.is_configured:
            return {
                "ready": False,
                "authenticated": False,
                "status_code": None,
                "warnings": ["Jira is not configured; set JIRA_BASE_URL, JIRA_PROJECT_KEY, JIRA_EMAIL, and JIRA_API_TOKEN."],
                "account": None,
            }

        logger.info("Jira auth check started")
        response = self.http_client.get_json(
            url=self._myself_url(),
            basic_auth=(self.config.email, self.config.api_token),
        )
        authenticated = 200 <= response.status_code < 300
        logger.info("Jira auth check completed status_code=%s authenticated=%s", response.status_code, authenticated)
        return {
            "ready": True,
            "authenticated": authenticated,
            "status_code": response.status_code,
            "warnings": self._warnings_for_response(response),
            "account": self._safe_account_summary(response.json_body) if authenticated else None,
        }

    def execute_action(self, story: dict) -> dict[str, Any]:
        payload = self.build_story_payload(story)
        if not self.config.is_configured:
            logger.info("Jira execution skipped because configuration is missing")
            return {
                "ready": False,
                "executed": False,
                "payload": payload,
                "created": {},
                "failed": [],
                "warnings": ["Jira is not configured; set JIRA_BASE_URL, JIRA_PROJECT_KEY, JIRA_EMAIL, and JIRA_API_TOKEN."],
                "status_code": None,
            }

        logger.info("Jira story creation started")
        story_result = self._create_issue(payload)
        story_key = story_result.get("key")
        warnings = list(story_result.get("warnings", []))
        if not story_key:
            logger.info("Jira story creation failed status_code=%s", story_result.get("status_code"))
            return {
                "ready": True,
                "executed": False,
                "payload": payload,
                "created": {},
                "failed": [{"type": "story", **story_result}],
                "warnings": warnings or ["Jira story creation failed."],
                "status_code": story_result.get("status_code"),
            }

        subtask_results = self._create_subtasks(story_key, story)
        created_subtasks = [result for result in subtask_results if result.get("key")]
        failed_subtasks = [result for result in subtask_results if not result.get("key")]
        logger.info(
            "Jira execution completed story_key=%s subtasks_created=%s subtasks_failed=%s",
            story_key,
            len(created_subtasks),
            len(failed_subtasks),
        )
        return {
            "ready": True,
            "executed": not failed_subtasks,
            "payload": payload,
            "created": {
                "story": self._created_issue_summary(story_result),
                "story_key": story_key,
                "subtasks": created_subtasks,
            },
            "failed": failed_subtasks,
            "warnings": warnings + [warning for result in failed_subtasks for warning in result.get("warnings", [])],
            "status_code": story_result.get("status_code"),
        }

    def _create_issue(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._post_with_retry(self._issue_url(), payload)
        body = response.json_body or {}
        key = body.get("key")
        warnings = self._warnings_for_response(response)
        return {
            "id": body.get("id"),
            "key": key,
            "self": body.get("self"),
            "url": self._browse_issue_url(str(key)) if key else "",
            "status_code": response.status_code,
            "warnings": warnings,
            "response": response.json_body,
        }

    def _create_subtasks(self, parent_key: str, story: dict) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for payload in self.build_subtask_payloads(parent_key, story):
            response = self._post_with_retry(self._issue_url(), payload)
            
            # Fallback for Atlassian Cloud which sometimes uses "Subtask" instead of "Sub-task"
            if response.status_code == 400 and payload["fields"]["issuetype"]["name"] == "Sub-task":
                payload["fields"]["issuetype"]["name"] = "Subtask"
                response = self._post_with_retry(self._issue_url(), payload)

            key = response.json_body.get("key") if response.json_body else None
            body = response.json_body or {}
            results.append(
                {
                    "id": body.get("id"),
                    "key": key,
                    "self": body.get("self"),
                    "url": self._browse_issue_url(str(key)) if key else "",
                    "summary": payload["fields"]["summary"],
                    "status_code": response.status_code,
                    "warnings": self._warnings_for_response(response),
                    "response": response.json_body,
                }
            )
        return results

    def _post_with_retry(self, url: str, payload: dict[str, Any]) -> HttpResponse:
        response = HttpResponse(status_code=0, text="No request attempted")
        for attempt in range(1, 4):
            response = self.http_client.post_json(
                url=url,
                payload=payload,
                basic_auth=(self.config.email, self.config.api_token),
                headers={"Accept": "application/json", "User-Agent": "ai-scrum-master/0.1"},
            )
            if response.status_code not in {0, 401, 429} and response.status_code < 500:
                return response
            logger.info("Jira request retryable status_code=%s attempt=%s", response.status_code, attempt)
        return response

    def _issue_url(self) -> str:
        return f"{self.config.base_url.rstrip('/')}/rest/api/3/issue"

    def _browse_issue_url(self, key: str) -> str:
        return f"{self.config.base_url.rstrip('/')}/browse/{key}"

    def _created_issue_summary(self, result: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": result.get("id"),
            "key": result.get("key"),
            "self": result.get("self"),
            "url": result.get("url") or (self._browse_issue_url(str(result["key"])) if result.get("key") else ""),
        }

    def _myself_url(self) -> str:
        return f"{self.config.base_url.rstrip('/')}/rest/api/3/myself"

    def _safe_account_summary(self, account: dict[str, Any] | None) -> dict[str, Any] | None:
        if not account:
            return None
        return {
            "account_id": account.get("accountId"),
            "display_name": account.get("displayName"),
            "email_address": account.get("emailAddress"),
        }

    def _warnings_for_response(self, response: HttpResponse) -> list[str]:
        if 200 <= response.status_code < 300:
            return []
        if response.status_code == 401:
            return ["Jira authorization failed after retries; alert PM to verify credentials."]
        if response.status_code == 429:
            return ["Jira rate limit persisted after retries."]
        if response.status_code >= 500:
            return ["Jira server error persisted after retries."]
        if response.status_code == 0:
            return [f"Jira request failed before receiving a response: {response.text}"]
        return [f"Jira request failed with status {response.status_code}."]

    def _build_adf_description(self, story: dict) -> dict[str, Any]:
        content = []

        # User Story
        content.append({
            "type": "heading",
            "attrs": {"level": 3},
            "content": [{"type": "text", "text": "User Story"}]
        })
        content.append({
            "type": "paragraph",
            "content": [{"type": "text", "text": story.get("user_story", "")}]
        })
        
        # Story Points
        if story.get("story_points"):
            content.append({
                "type": "panel",
                "attrs": {"panelType": "info"},
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": f"Story Points: {story.get('story_points')}"}]
                }]
            })

        # Acceptance Criteria
        ac_list = story.get("acceptance_criteria", [])
        if ac_list:
            content.append({
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "Acceptance Criteria"}]
            })
            ac_items = []
            for ac in ac_list:
                ac_text = str(ac)
                ac_items.append({
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": [{"type": "text", "text": ac_text}]
                    }]
                })
            content.append({
                "type": "bulletList",
                "content": ac_items
            })

        # Definition of Done
        dod_list = story.get("definition_of_done", [])
        if dod_list:
            content.append({
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "Definition of Done"}]
            })
            dod_items = []
            for dod in dod_list:
                dod_items.append({
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": [{"type": "text", "text": str(dod)}]
                    }]
                })
            content.append({
                "type": "bulletList",
                "content": dod_items
            })

        return {
            "version": 1,
            "type": "doc",
            "content": content
        }

    def _build_text_adf(self, text: str) -> dict[str, Any]:
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text}],
                }
            ],
        }
