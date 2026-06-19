from fastapi import APIRouter
from typing import Any

from ai_scrum_master.core.utils.database import DatabaseManager

router = APIRouter()

@router.get("/history", response_model=list[dict[str, Any]])
def get_project_history(project_id: str | None = None, limit: int = 50):
    return DatabaseManager.get_history(project_id, limit)

@router.delete("/history/{history_id}")
def delete_history_record(history_id: str):
    from fastapi import HTTPException
    success = DatabaseManager.delete_history(history_id)
    if not success:
        raise HTTPException(status_code=404, detail="History record not found or could not be deleted")
    return {"success": True}
