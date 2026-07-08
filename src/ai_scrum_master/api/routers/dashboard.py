from typing import Optional

from fastapi import APIRouter

from ai_scrum_master.api.responses import build_envelope_response
from ai_scrum_master.api.schemas import ApiResponseEnvelope
from ai_scrum_master.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
dashboard_service = DashboardService()


@router.get("/management", response_model=ApiResponseEnvelope)
def get_management_dashboard(project_id: Optional[str] = None):
    return build_envelope_response(
        endpoint="management",
        data=dashboard_service.get_management_dashboard(project_id),
        project_id=project_id,
    )


@router.get("/analytics", response_model=ApiResponseEnvelope)
def get_analytics_overview(project_id: Optional[str] = None):
    return build_envelope_response(
        endpoint="analytics",
        data=dashboard_service.get_analytics_overview(project_id),
        project_id=project_id,
    )


@router.get("/team", response_model=ApiResponseEnvelope)
def get_team_members(project_id: Optional[str] = None):
    return build_envelope_response(
        endpoint="team",
        data=dashboard_service.get_team_members(project_id),
        project_id=project_id,
    )
