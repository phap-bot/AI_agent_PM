from fastapi import APIRouter
from typing import Any

from ai_scrum_master.core.database import DatabaseManager

router = APIRouter()

@router.get("/history", response_model=list[dict[str, Any]])
def get_project_history(project_id: str | None = None, limit: int = 50):
    return DatabaseManager.get_history(project_id, limit)
