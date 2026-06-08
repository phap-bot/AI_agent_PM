from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Optional
from bson import ObjectId

from ai_scrum_master.core.database import DatabaseManager

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

class ProjectCreateModel(BaseModel):
    name: str
    description: str = ""

class ProjectUpdateModel(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    jira_config: Optional[JiraConfigModel] = None
    slack_config: Optional[SlackConfigModel] = None

def serialize_project(project: dict) -> dict:
    if "_id" in project:
        project["id"] = str(project["_id"])
        del project["_id"]
    return project

@router.get("", response_model=list[dict[str, Any]])
def get_projects():
    projects = DatabaseManager.get_all_projects()
    return [serialize_project(p) for p in projects]

@router.get("/{project_id}", response_model=dict[str, Any])
def get_project(project_id: str):
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
    project = DatabaseManager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return serialize_project(project)

@router.get("/{project_id}/jira-priorities", response_model=list[dict[str, Any]])
def get_project_jira_priorities(project_id: str):
    from ai_scrum_master.actions.jira import JiraTool
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    jira = JiraTool.from_project(project_id)
    return jira.get_priorities()

@router.post("", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreateModel):
    project_data = data.model_dump()
    project_data["jira_config"] = {}
    project_data["slack_config"] = {}
    
    # Check for duplicate name
    existing = DatabaseManager.get_projects_collection().find_one({"name": data.name})
    if existing:
        raise HTTPException(status_code=400, detail="Project name already exists")
        
    project_id = DatabaseManager.create_project(project_data)
    if not project_id:
        raise HTTPException(status_code=500, detail="Failed to create project")
    return get_project(project_id)

@router.put("/{project_id}", response_model=dict[str, Any])
def update_project(project_id: str, data: ProjectUpdateModel):
    if not ObjectId.is_valid(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID")
        
    project = DatabaseManager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return serialize_project(project)
        
    success = DatabaseManager.update_project(project_id, updates)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update project")
        
    return get_project(project_id)
