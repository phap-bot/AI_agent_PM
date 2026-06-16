from fastapi import APIRouter, Query
from typing import Any, Optional

from ai_scrum_master.actions.jira import JiraTool
from ai_scrum_master.core.config.settings import get_settings

router = APIRouter()

@router.get("/sprint", response_model=dict[str, Any])
def get_sprint_board(project_id: Optional[str] = Query(None)):
    if project_id:
        jira = JiraTool.from_project(project_id)
    else:
        jira = JiraTool()
        
    # We should get board_id from project config if available
    board_id = jira.config.board_id
    
    if not board_id:
        return {"error": "JIRA_BOARD_ID is not configured"}
        
    sprint_id = jira._get_active_sprint(board_id)
    if not sprint_id:
        return {"error": "No active sprint found"}
        
    # Get sprint details
    sprint_url = f"{jira.config.base_url.rstrip('/')}/rest/agile/1.0/sprint/{sprint_id}"
    sprint_resp = jira.http_client.get_json(
        url=sprint_url,
        basic_auth=(jira.config.email, jira.config.api_token),
        headers={"Accept": "application/json"}
    )
    sprint_data = sprint_resp.json_body if sprint_resp.status_code == 200 else {"id": sprint_id, "name": f"Sprint {sprint_id}"}
        
    # Get issues in sprint
    url = f"{jira.config.base_url.rstrip('/')}/rest/agile/1.0/board/{board_id}/sprint/{sprint_id}/issue"
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
