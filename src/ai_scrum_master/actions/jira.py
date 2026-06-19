from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_scrum_master.core.config.settings import get_settings
from ai_scrum_master.core.utils.http_client import HttpClient, HttpResponse, UrllibHttpClient
from ai_scrum_master.core.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class JiraConfig:
    base_url: str
    project_key: str
    email: str
    api_token: str
    issue_type: str = "Task"
    subtask_issue_type: str = "Sub-task"
    board_id: str = ""

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
            board_id=settings.jira_board_id,
        )
        self.http_client = http_client or UrllibHttpClient()

    @classmethod
    def from_project(cls, project_id: str | None, http_client: HttpClient | None = None) -> JiraTool:
        if not project_id:
            return cls(http_client=http_client)
            
        from ai_scrum_master.core.utils.database import DatabaseManager
        project = DatabaseManager.get_project(project_id)
        if not project or not project.get("jira_config"):
            return cls(http_client=http_client)
            
        db_config = project["jira_config"]
        settings = get_settings()
        config = JiraConfig(
            base_url=db_config.get("base_url") or settings.jira_base_url,
            project_key=db_config.get("project_key") or settings.jira_project_key,
            email=db_config.get("email") or settings.jira_email,
            api_token=db_config.get("api_token") or settings.jira_api_token,
            issue_type=db_config.get("issue_type") or settings.jira_issue_type,
            subtask_issue_type=db_config.get("subtask_issue_type") or settings.jira_subtask_issue_type,
            board_id=db_config.get("board_id") or settings.jira_board_id,
        )
        return cls(config=config, http_client=http_client)

    def build_story_payload(self, story: dict) -> dict[str, Any]:
        payload = {
            "fields": {
                "project": {"key": self.config.project_key},
                "summary": story["title"],
                "description": self._build_adf_description(story),
                "issuetype": {"name": self.config.issue_type},
                "labels": ["ai-scrum-master"],
            }
        }
        
        if "priority" in story and story["priority"]:
            payload["fields"]["priority"] = {"name": story["priority"]}
            
        return payload

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
        
        # Create story splits if any
        story_splits_results = []
        created_splits = []
        if story.get("story_splits"):
            logger.info("Jira creating %s story splits", len(story.get("story_splits", [])))
            for split in story.get("story_splits", []):
                if not split.get("priority") and story.get("priority"):
                    split["priority"] = story["priority"]
                split_payload = self.build_story_payload(split)
                split_payload["fields"]["labels"].append("split-story")
                
                split_result = self._create_issue(split_payload)
                split_key = split_result.get("key")
                
                split_subtasks_created = []
                if split_key:
                    split_subtask_results = self._create_subtasks(split_key, split)
                    split_subtasks_created = [r for r in split_subtask_results if r.get("key")]
                    failed_subtasks.extend([r for r in split_subtask_results if not r.get("key")])
                    created_splits.append(split_key)
                    
                story_splits_results.append({
                    "story": self._created_issue_summary(split_result),
                    "story_key": split_key,
                    "subtasks": split_subtasks_created
                })

        logger.info(
            "Jira execution completed story_key=%s subtasks_created=%s subtasks_failed=%s splits_created=%s",
            story_key,
            len(created_subtasks),
            len(failed_subtasks),
            len(created_splits)
        )
        
        if self.config.board_id and (story_key or created_splits):
            logger.info("Attempting to move stories to sprint on board %s", self.config.board_id)
            try:
                sprints = story.get("sprint_allocation", [])
                target_sprint_name = None
                if sprints and len(sprints) > 0:
                    if isinstance(sprints[0], dict):
                        target_sprint_name = sprints[0].get("name") or str(sprints[0])
                    else:
                        target_sprint_name = str(sprints[0])
                        
                if target_sprint_name:
                    logger.info("AI suggested sprint allocation: %s", target_sprint_name)
                    sprint_id = self._get_or_create_sprint_by_name(self.config.board_id, target_sprint_name)
                    if sprint_id:
                        keys_to_move = []
                        if story_key:
                            keys_to_move.append(story_key)
                        keys_to_move.extend(created_splits)
                        for key in keys_to_move:
                            self._move_issue_to_sprint(sprint_id, key)
                        logger.info("Stories successfully moved to sprint %s (%s)", target_sprint_name, sprint_id)
                    else:
                        logger.warning("Failed to resolve sprint %s. Attempting fallback to active sprint.", target_sprint_name)
                        sprint_id = self._get_active_sprint(self.config.board_id)
                        if sprint_id:
                            keys_to_move = []
                            if story_key:
                                keys_to_move.append(story_key)
                            keys_to_move.extend(created_splits)
                            for key in keys_to_move:
                                self._move_issue_to_sprint(sprint_id, key)
                            logger.info("Stories successfully moved to active sprint %s", sprint_id)
                        else:
                            logger.info("No active sprint found. Stories remain in backlog.")
                else:
                    logger.info("No sprint_allocation provided by AI. Attempting fallback to active sprint.")
                    sprint_id = self._get_active_sprint(self.config.board_id)
                    if sprint_id:
                        keys_to_move = []
                        if story_key:
                            keys_to_move.append(story_key)
                        keys_to_move.extend(created_splits)
                        for key in keys_to_move:
                            self._move_issue_to_sprint(sprint_id, key)
                        logger.info("Stories successfully moved to active sprint %s", sprint_id)
                    else:
                        logger.info("No active sprint found. Stories remain in backlog.")
            except Exception as e:
                msg = f"Failed to move stories to sprint: {e}"
                logger.warning(msg)
                warnings.append(msg)
        return {
            "ready": True,
            "executed": not failed_subtasks,
            "payload": payload,
            "created": {
                "story": self._created_issue_summary(story_result),
                "story_key": story_key,
                "subtasks": created_subtasks,
                "story_splits": story_splits_results,
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

    def get_priorities(self) -> list[dict[str, Any]]:
        """Fetch available priorities from Jira."""
        if not self.config.is_configured:
            return []
            
        url = f"{self.config.base_url.rstrip('/')}/rest/api/2/priority"
        response = self.http_client.get_json(
            url=url,
            basic_auth=(self.config.email, self.config.api_token),
            headers={"Accept": "application/json"}
        )
        if response.status_code == 200 and isinstance(response.json_body, list):
            return [
                {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "iconUrl": p.get("iconUrl"),
                }
                for p in response.json_body
            ]
        return []

    def _get_active_sprint(self, board_id: str) -> int | None:
        url = f"{self.config.base_url.rstrip('/')}/rest/agile/1.0/board/{board_id}/sprint?state=active"
        response = self.http_client.get_json(
            url=url,
            basic_auth=(self.config.email, self.config.api_token),
            headers={"Accept": "application/json"}
        )
        if response.status_code == 200 and response.json_body:
            values = response.json_body.get("values", [])
            if values:
                return values[0].get("id")
        return None

    def _get_or_create_sprint_by_name(self, board_id: str, sprint_name: str) -> int | None:
        url = f"{self.config.base_url.rstrip('/')}/rest/agile/1.0/board/{board_id}/sprint"
        response = self.http_client.get_json(
            url=url,
            basic_auth=(self.config.email, self.config.api_token),
            headers={"Accept": "application/json"}
        )
        if response.status_code == 200 and response.json_body:
            values = response.json_body.get("values", [])
            for sprint in values:
                if sprint.get("name", "").lower() == sprint_name.lower():
                    return sprint.get("id")
                    
        # If not found, create it
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=14)
        payload = {
            "name": sprint_name,
            "startDate": now.isoformat(timespec='milliseconds').replace("+00:00", "+0000"),
            "endDate": end.isoformat(timespec='milliseconds').replace("+00:00", "+0000"),
            "originBoardId": int(board_id)
        }
        create_url = f"{self.config.base_url.rstrip('/')}/rest/agile/1.0/sprint"
        create_resp = self._post_with_retry(create_url, payload)
        if create_resp.status_code in [200, 201] and create_resp.json_body:
            return create_resp.json_body.get("id")
            
        logger.warning("Failed to auto-create sprint '%s': status=%s body=%s", sprint_name, create_resp.status_code, create_resp.text)
        return None

    def _move_issue_to_sprint(self, sprint_id: int, issue_key: str) -> None:
        url = f"{self.config.base_url.rstrip('/')}/rest/agile/1.0/sprint/{sprint_id}/issue"
        payload = {"issues": [issue_key]}
        response = self._post_with_retry(url, payload)
        if response.status_code not in (200, 204):
            raise Exception(f"Jira API returned {response.status_code}: {response.text}")

    def _post_with_retry(self, url: str, payload: dict[str, Any]) -> HttpResponse:
        import time
        response = HttpResponse(status_code=0, text="No request attempted")
        max_attempts = 4
        base_delay = 1.0
        
        for attempt in range(1, max_attempts + 1):
            response = self.http_client.post_json(
                url=url,
                payload=payload,
                basic_auth=(self.config.email, self.config.api_token),
                headers={"Accept": "application/json", "User-Agent": "ai-scrum-master/0.1"},
            )
            if response.status_code not in {0, 401, 429} and response.status_code < 500:
                return response
                
            if attempt < max_attempts:
                delay = base_delay * (2 ** (attempt - 1))
                logger.info("Jira request retryable status_code=%s attempt=%s, sleeping %.1fs", response.status_code, attempt, delay)
                time.sleep(delay)
            else:
                logger.warning("Jira request failed after max attempts status_code=%s", response.status_code)
                
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
