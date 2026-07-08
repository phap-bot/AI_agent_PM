from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ai_scrum_master.api.responses import build_envelope_response
from ai_scrum_master.api.schemas import ApiResponseEnvelope
from ai_scrum_master.core.utils.database import DatabaseManager

router = APIRouter(prefix="/projects", tags=["projects"])


class JiraConfigModel(BaseModel):
    base_url: str = ""
    project_key: str = ""
    email: str = ""
    api_token: str = ""
    issue_type: str = "Task"
    subtask_issue_type: str = "Sub-task"
    board_id: str = ""


class SlackConfigModel(BaseModel):
    webhook_url: str = ""
    mention_user_id: str = ""
    dev_channel_id: str = ""
    qa_channel_id: str = ""


class GithubConfigModel(BaseModel):
    repository: str = ""
    base_branch: str = "main"
    api_token: str = Field(default="", description="Get token at: https://github.com/settings/tokens/new")


class ProjectCreateModel(BaseModel):
    name: str
    description: str = ""


class ProjectUpdateModel(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    jira_config: Optional[JiraConfigModel] = None
    slack_config: Optional[SlackConfigModel] = None
    github_config: Optional[GithubConfigModel] = None


def serialize_project(project: dict) -> dict:
    serialized = dict(project)
    if "_id" in serialized:
        serialized["id"] = str(serialized["_id"])
        del serialized["_id"]
    return serialized


def _validate_project_id(project_id: str) -> None:
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")


@router.get("", response_model=ApiResponseEnvelope)
def get_projects():
    projects = DatabaseManager.get_all_projects()
    return build_envelope_response(
        endpoint="projects_list",
        data=[serialize_project(project) for project in projects],
    )


@router.get("/{project_id}", response_model=ApiResponseEnvelope)
def get_project(project_id: str):
    _validate_project_id(project_id)
    project = DatabaseManager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return build_envelope_response(
        endpoint="project_detail",
        project_id=project_id,
        data=serialize_project(project),
    )


@router.get("/{project_id}/jira-priorities", response_model=ApiResponseEnvelope)
def get_project_jira_priorities(project_id: str):
    from ai_scrum_master.actions.jira import JiraTool

    _validate_project_id(project_id)
    jira = JiraTool.from_project(project_id)
    return build_envelope_response(
        endpoint="project_jira_priorities",
        project_id=project_id,
        data=jira.get_priorities(),
    )


@router.post("", response_model=ApiResponseEnvelope, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreateModel):
    project_data = data.model_dump()
    project_data["jira_config"] = {}
    project_data["slack_config"] = {}
    project_data["github_config"] = {}

    if DatabaseManager.project_name_exists(data.name):
        raise HTTPException(status_code=400, detail="Project name already exists")

    project_id = DatabaseManager.create_project(project_data)
    if not project_id:
        raise HTTPException(status_code=500, detail="Failed to create project")

    project = DatabaseManager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=500, detail="Created project could not be loaded")

    return build_envelope_response(
        endpoint="project_create",
        project_id=project_id,
        data=serialize_project(project),
    )


@router.put("/{project_id}", response_model=ApiResponseEnvelope)
def update_project(project_id: str, data: ProjectUpdateModel):
    _validate_project_id(project_id)

    project = DatabaseManager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return build_envelope_response(
            endpoint="project_update",
            project_id=project_id,
            data=serialize_project(project),
        )

    new_name = updates.get("name")
    if new_name and DatabaseManager.project_name_exists(new_name, exclude_project_id=project_id):
        raise HTTPException(status_code=400, detail="Project name already exists")

    success = DatabaseManager.update_project(project_id, updates)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update project")

    updated_project = DatabaseManager.get_project(project_id)
    if not updated_project:
        raise HTTPException(status_code=500, detail="Updated project could not be loaded")

    return build_envelope_response(
        endpoint="project_update",
        project_id=project_id,
        data=serialize_project(updated_project),
    )


@router.delete("/{project_id}", response_model=ApiResponseEnvelope)
def delete_project(project_id: str):
    _validate_project_id(project_id)

    project = DatabaseManager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    success = DatabaseManager.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete project")

    return build_envelope_response(
        endpoint="project_delete",
        project_id=project_id,
        data={"deleted": True, "project_id": project_id},
    )
