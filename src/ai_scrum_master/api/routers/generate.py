from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter
from celery.result import AsyncResult

from ai_scrum_master.api.responses import build_envelope_response
from ai_scrum_master.api.schemas import ApiResponseEnvelope, GenerateJobResponse, GenerateStatusResponse, GenerateStoriesRequest
from ai_scrum_master.core.utils.database import DatabaseManager
from ai_scrum_master.worker.celery_app import celery_app
from ai_scrum_master.worker.tasks import generate_story_task

router = APIRouter()

@router.post("/generate", response_model=ApiResponseEnvelope)
def generate_stories(
    payload: GenerateStoriesRequest,
) -> ApiResponseEnvelope:
    # Trigger Celery task
    task = cast(Any, generate_story_task).delay(
        requirement=payload.requirement,
        n_results=payload.n_results,
        allow_fallback=payload.allow_fallback_without_context,
        forced_docs=payload.forced_context_docs or None,
        project_id=payload.project_id,
        user_id=payload.user_id,
    )
    DatabaseManager.create_job(
        job_id=task.id,
        requirement=payload.requirement,
        project_id=payload.project_id,
        user_id=payload.user_id,
    )
    return build_envelope_response(
        endpoint="generate_create",
        project_id=payload.project_id,
        data=GenerateJobResponse(job_id=task.id).model_dump(),
    )


@router.post("/generate/cancel/{job_id}", response_model=ApiResponseEnvelope)
def cancel_generate_job(job_id: str) -> ApiResponseEnvelope:
    job = DatabaseManager.get_job(job_id)
    project_id = job.get("project_id") if job else None
    already_finished = job and job.get("status") in {"completed", "failed", "cancelled"}

    if not already_finished:
        celery_app.control.revoke(job_id, terminate=True, signal="SIGTERM")
        DatabaseManager.update_job(
            job_id,
            status="cancelled",
            stage="cancelled",
            message="Generation cancelled by client.",
            error="client_cancelled",
        )

    return build_envelope_response(
        endpoint="generate_cancel",
        project_id=project_id,
        data={
            "job_id": job_id,
            "status": "cancelled" if not already_finished else job.get("status"),
            "cancelled": not already_finished or job.get("status") == "cancelled",
        },
    )

@router.get("/generate/status/{job_id}", response_model=ApiResponseEnvelope)
def get_generate_status(job_id: str) -> ApiResponseEnvelope:
    job = DatabaseManager.get_job(job_id)
    if job:
        status_payload = GenerateStatusResponse(
            job_id=job_id,
            status=job.get("status", "processing"),
            stage=job.get("stage", "processing"),
            message=job.get("message", ""),
            partial_result=job.get("partial_result") or {},
            result=job.get("result"),
        )
        return build_envelope_response(
            endpoint="generate_status",
            project_id=job.get("project_id"),
            data=status_payload.model_dump(),
        )

    task_result = AsyncResult(job_id, app=celery_app)
    
    if task_result.state == 'PENDING':
        status_payload = GenerateStatusResponse(
            job_id=job_id,
            status="processing",
            stage="pending",
            message="Task is pending...",
            partial_result={},
            result=None
        )
    elif task_result.state == 'STARTED':
        status_payload = GenerateStatusResponse(
            job_id=job_id,
            status="processing",
            stage="started",
            message="Task has started...",
            partial_result={},
            result=None
        )
    elif task_result.state == 'PROCESSING':
        meta = task_result.info or {}
        status_payload = GenerateStatusResponse(
            job_id=job_id,
            status="processing",
            stage=meta.get("stage", "processing"),
            message="Task is in progress...",
            partial_result=meta.get("partial_result", {}),
            result=None
        )
    elif task_result.state == 'SUCCESS':
        status_payload = GenerateStatusResponse(
            job_id=job_id,
            status="completed",
            stage="completed",
            message="Task completed successfully.",
            partial_result={},
            result=task_result.result
        )
    elif task_result.state == 'FAILURE':
        status_payload = GenerateStatusResponse(
            job_id=job_id,
            status="failed",
            stage="failed",
            message=str(task_result.info),
            partial_result={},
            result=None
        )
    elif task_result.state == 'REVOKED':
        status_payload = GenerateStatusResponse(
            job_id=job_id,
            status="cancelled",
            stage="cancelled",
            message="Generation cancelled by client.",
            partial_result={},
            result=None
        )
    else:
        status_payload = GenerateStatusResponse(
            job_id=job_id,
            status="failed",
            stage="unknown",
            message=f"Unknown task state: {task_result.state}",
            partial_result={},
            result=None
        )
    return build_envelope_response(
        endpoint="generate_status",
        project_id=None,
        data=status_payload.model_dump(),
    )
