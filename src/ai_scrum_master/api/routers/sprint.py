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
    url = f"{jira.config.base_url.rstrip('/')}/rest/agile/1.0/board/{board_id}/sprint/{sprint_id}/issue?maxResults=500"
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
                "assignee": fields.get("assignee"),
                "parent_key": fields.get("parent", {}).get("key")
            })
            
        # Also fetch subtasks of these issues
        parent_keys = [i["key"] for i in mapped_issues]
        if parent_keys:
            import urllib.parse
            # chunk parent_keys to avoid URL too long if there are many
            chunked_parents = [parent_keys[i:i + 50] for i in range(0, len(parent_keys), 50)]
            for chunk in chunked_parents:
                jql = f"parent in ({','.join(chunk)})"
                sub_url = f"{jira.config.base_url.rstrip('/')}/rest/agile/1.0/board/{board_id}/issue?jql={urllib.parse.quote(jql)}&maxResults=500"
                sub_resp = jira.http_client.get_json(
                    url=sub_url,
                    basic_auth=(jira.config.email, jira.config.api_token),
                    headers={"Accept": "application/json"}
                )
                if sub_resp.status_code == 200:
                    for sub in sub_resp.json_body.get("issues", []):
                        fields = sub.get("fields", {})
                        # Avoid duplicates if a subtask was somehow already returned
                        if not any(x["key"] == sub["key"] for x in mapped_issues):
                            mapped_issues.append({
                                "key": sub.get("key"),
                                "summary": fields.get("summary"),
                                "status": fields.get("status", {}).get("name", ""),
                                "type": fields.get("issuetype", {}).get("name", ""),
                                "assignee": fields.get("assignee"),
                                "parent_key": fields.get("parent", {}).get("key")
                            })

        return {
            "sprint": sprint_data,
            "issues": mapped_issues
        }
        
    return {"error": f"Failed to fetch sprint issues: {response.text}"}

@router.post("/sprint", response_model=dict[str, Any])
def create_new_sprint(project_id: Optional[str] = Query(None)):
    if project_id:
        jira = JiraTool.from_project(project_id)
    else:
        jira = JiraTool()
        
    board_id = jira.config.board_id
    if not board_id:
        return {"error": "JIRA_BOARD_ID is not configured"}
        
    import requests
    from datetime import datetime, timedelta, timezone
    
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=14) # 2 weeks
    
    payload = {
        "name": f"AI Auto Sprint {now.strftime('%d%m')}",
        "startDate": now.isoformat(timespec='milliseconds').replace("+00:00", "+0000"),
        "endDate": end.isoformat(timespec='milliseconds').replace("+00:00", "+0000"),
        "originBoardId": int(board_id)
    }
    
    url = f"{jira.config.base_url.rstrip('/')}/rest/agile/1.0/sprint"
    resp = requests.post(
        url,
        json=payload,
        auth=(jira.config.email, jira.config.api_token),
        headers={"Accept": "application/json"}
    )
    
    if resp.status_code in [200, 201]:
        return {"message": "Sprint created", "sprint": resp.json()}
    return {"error": f"Failed to create sprint: {resp.text}"}

@router.post("/sprint/{sprint_id}/complete", response_model=dict[str, Any])
def complete_sprint(sprint_id: int, project_id: Optional[str] = Query(None)):
    if project_id:
        jira = JiraTool.from_project(project_id)
    else:
        jira = JiraTool()
        
    board_id = jira.config.board_id
    if not board_id:
        return {"error": "JIRA_BOARD_ID is not configured"}
        
    import requests
    
    payload = {
        "state": "closed"
    }
    
    url = f"{jira.config.base_url.rstrip('/')}/rest/agile/1.0/sprint/{sprint_id}"
    resp = requests.post(
        url,
        json=payload,
        auth=(jira.config.email, jira.config.api_token),
        headers={"Accept": "application/json"}
    )
    
    if resp.status_code in [200, 204]:
        return {"message": "Sprint completed successfully", "success": True}
    return {"error": f"Failed to complete sprint: {resp.text}", "success": False}

@router.delete("/sprint/issue/{issue_key}", response_model=dict[str, Any])
def delete_issue(issue_key: str, project_id: Optional[str] = Query(None)):
    if project_id:
        jira = JiraTool.from_project(project_id)
    else:
        jira = JiraTool()
    return jira.delete_issue(issue_key)

from pydantic import BaseModel
class TransitionRequest(BaseModel):
    status: str

@router.put("/sprint/issue/{issue_key}/status", response_model=dict[str, Any])
def transition_issue(issue_key: str, req: TransitionRequest, project_id: Optional[str] = Query(None)):
    if project_id:
        jira = JiraTool.from_project(project_id)
    else:
        jira = JiraTool()
    return jira.transition_issue(issue_key, req.status)
