from typing import Any, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ai_scrum_master.actions.jira import JiraTool
from ai_scrum_master.api.responses import build_envelope_response
from ai_scrum_master.api.schemas import ApiResponseEnvelope
from ai_scrum_master.core.utils.exceptions import BusinessRuleError, IntegrationError

router = APIRouter()


def _jira_for_project(project_id: Optional[str]) -> JiraTool:
    if project_id:
        return JiraTool.from_project(project_id)
    return JiraTool()


def _raise_sprint_error(result: dict[str, Any], *, default_message: str) -> None:
    message = result.get("error") or default_message
    details = {k: v for k, v in result.items() if k != "success"}
    if any(token in message for token in ("not configured", "No active sprint found", "No transition to", "JIRA_BOARD_ID")):
        raise BusinessRuleError(message=message, details=details)
    raise IntegrationError(message=message, service_name="jira", details=details)


@router.get("/sprint", response_model=ApiResponseEnvelope)
def get_sprint_board(project_id: Optional[str] = Query(None)):
    jira = _jira_for_project(project_id)
    result = jira.get_sprint_board()
    if not result.get("success"):
        _raise_sprint_error(result, default_message="Failed to fetch sprint board")
    return build_envelope_response(
        endpoint="board",
        data={"sprint": result["sprint"], "issues": result["issues"]},
        project_id=project_id,
    )


@router.post("/sprint", response_model=ApiResponseEnvelope)
def create_new_sprint(project_id: Optional[str] = Query(None)):
    jira = _jira_for_project(project_id)
    result = jira.create_sprint()
    if not result.get("success"):
        _raise_sprint_error(result, default_message="Failed to create sprint")
    return build_envelope_response(
        endpoint="create",
        data={"message": result["message"], "sprint": result["sprint"]},
        project_id=project_id,
    )


class CompleteSprintRequest(BaseModel):
    move_open_to: str = "backlog"
    open_issues: list[str] = []


@router.post("/sprint/{sprint_id}/complete", response_model=ApiResponseEnvelope)
def complete_sprint(
    sprint_id: int,
    payload: CompleteSprintRequest,
    project_id: Optional[str] = Query(None),
):
    jira = _jira_for_project(project_id)
    result = jira.complete_sprint(
        sprint_id=sprint_id,
        move_open_to=payload.move_open_to,
        open_issues=payload.open_issues,
    )
    if not result.get("success"):
        _raise_sprint_error(result, default_message="Failed to complete sprint")
    return build_envelope_response(endpoint="complete", data=result, project_id=project_id)


@router.delete("/sprint/issue/{issue_key}", response_model=ApiResponseEnvelope)
def delete_issue(issue_key: str, project_id: Optional[str] = Query(None)):
    jira = _jira_for_project(project_id)
    result = jira.delete_issue(issue_key)
    if not result.get("success"):
        _raise_sprint_error(result, default_message="Failed to delete issue")
    return build_envelope_response(endpoint="delete_issue", data=result, project_id=project_id)


class TransitionRequest(BaseModel):
    status: str


@router.put("/sprint/issue/{issue_key}/status", response_model=ApiResponseEnvelope)
def transition_issue(issue_key: str, req: TransitionRequest, project_id: Optional[str] = Query(None)):
    jira = _jira_for_project(project_id)
    result = jira.transition_issue(issue_key, req.status)
    if not result.get("success"):
        _raise_sprint_error(result, default_message="Failed to change issue status")
    return build_envelope_response(endpoint="transition_issue", data=result, project_id=project_id)
