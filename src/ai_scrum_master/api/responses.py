from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ai_scrum_master.api.schemas import ApiResponseEnvelope, ApiResponseMeta


def build_envelope_response(*, endpoint: str, data: dict[str, Any], project_id: str | None = None) -> ApiResponseEnvelope:
    return ApiResponseEnvelope(
        success=True,
        data=data,
        meta=ApiResponseMeta(
            endpoint=endpoint,
            project_id=project_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
        ),
    )
