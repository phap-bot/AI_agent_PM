from fastapi import APIRouter, Query
from typing import Any, Optional

from ai_scrum_master.actions.jira import JiraTool
from ai_scrum_master.core.config import get_settings

router = APIRouter()

@router.get("/sprint", response_model=dict[str, Any])
def get_sprint_board(project_id: Optional[str] = Query(None)):
    if project_id:
        jira = JiraTool.from_project(project_id)
    else:
        jira = JiraTool()
        
    settings = get_settings()
    
    # We should get board_id from project config if available, otherwise fallback to env
    # Currently jira_config in DB doesn't have board_id explicitly, maybe we use the one from env
    # or let's assume it's in the env for now.
    # Ideally, board_id would be in JiraConfig.
    
    if not settings.jira_board_id:
        return {"error": "JIRA_BOARD_ID is not configured"}
        
    sprint_data = jira._get_active_sprint(settings.jira_board_id)
    if not sprint_data:
        return {"error": "No active sprint found"}
        
    sprint_id = sprint_data.get("id")
        
    # Get issues in sprint
    url = f"{jira.config.base_url.rstrip('/')}/rest/agile/1.0/board/{settings.jira_board_id}/sprint/{sprint_id}/issue"
    response = jira.http_client.get_json(
        url=url,
        basic_auth=(jira.config.email, jira.config.api_token),
        headers={"Accept": "application/json"}
    )
    
    if response.status_code == 200:
        raw_issues = response.json_body.get("issues", [])
        mapped_issues = []
        for issue in raw_issues:
            fields = issue.get("fields", {})
            mapped_issues.append({
                "key": issue.get("key"),
                "summary": fields.get("summary"),
                "status": fields.get("status", {}).get("name", ""),
                "type": fields.get("issuetype", {}).get("name", ""),
                "assignee": fields.get("assignee")
            })
        return {
            "sprint": sprint_data,
            "issues": mapped_issues
        }
        
    return {"error": f"Failed to fetch sprint issues: {response.text}"}
