from fastapi import APIRouter, HTTPException

from ai_scrum_master.api.responses import build_envelope_response
from ai_scrum_master.api.schemas import ApiResponseEnvelope
from ai_scrum_master.core.utils.database import DatabaseManager

router = APIRouter()


@router.get("/history", response_model=ApiResponseEnvelope)
def get_project_history(project_id: str | None = None, limit: int = 50):
    return build_envelope_response(
        endpoint="history_list",
        project_id=project_id,
        data=DatabaseManager.get_history(project_id, limit),
    )


@router.delete("/history/{history_id}", response_model=ApiResponseEnvelope)
def delete_history_record(history_id: str):
    success = DatabaseManager.delete_history(history_id)
    if not success:
        raise HTTPException(status_code=404, detail="History record not found or could not be deleted")
    return build_envelope_response(
        endpoint="history_delete",
        data={"deleted": True, "history_id": history_id},
    )
