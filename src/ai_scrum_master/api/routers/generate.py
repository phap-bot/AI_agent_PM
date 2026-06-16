from __future__ import annotations

from fastapi import APIRouter, Depends

from ai_scrum_master.api.schemas import GenerateStoriesRequest, GenerateStoriesResponse

router = APIRouter()


from ai_scrum_master.api.schemas import GenerateJobResponse, GenerateStatusResponse
from ai_scrum_master.worker.tasks import generate_story_task
from celery.result import AsyncResult

@router.post("/generate", response_model=GenerateJobResponse)
def generate_stories(
    payload: GenerateStoriesRequest,
) -> GenerateJobResponse:
    # Trigger Celery task
    task = generate_story_task.delay(
        requirement=payload.requirement,
        n_results=payload.n_results,
        allow_fallback=payload.allow_fallback_without_context,
        forced_docs=payload.forced_context_docs or None,
        project_id=payload.project_id
    )
    return GenerateJobResponse(job_id=task.id)


from ai_scrum_master.worker.celery_app import celery_app

@router.get("/generate/status/{job_id}", response_model=GenerateStatusResponse)
def get_generate_status(job_id: str) -> GenerateStatusResponse:
    task_result = AsyncResult(job_id, app=celery_app)
    
    if task_result.state == 'PENDING':
        return GenerateStatusResponse(
            job_id=job_id,
            status="processing",
            stage="pending",
            message="Task is pending...",
            partial_result={},
            result=None
        )
    elif task_result.state == 'STARTED':
        return GenerateStatusResponse(
            job_id=job_id,
            status="processing",
            stage="started",
            message="Task has started...",
            partial_result={},
            result=None
        )
    elif task_result.state == 'PROCESSING':
        meta = task_result.info or {}
        return GenerateStatusResponse(
            job_id=job_id,
            status="processing",
            stage=meta.get("stage", "processing"),
            message="Task is in progress...",
            partial_result=meta.get("partial_result", {}),
            result=None
        )
    elif task_result.state == 'SUCCESS':
        return GenerateStatusResponse(
            job_id=job_id,
            status="completed",
            stage="completed",
            message="Task completed successfully.",
            partial_result={},
            result=task_result.result
        )
    elif task_result.state == 'FAILURE':
        return GenerateStatusResponse(
            job_id=job_id,
            status="failed",
            stage="failed",
            message=str(task_result.info),
            partial_result={},
            result=None
        )
    else:
        return GenerateStatusResponse(
            job_id=job_id,
            status="failed",
            stage="unknown",
            message=f"Unknown task state: {task_result.state}",
            partial_result={},
            result=None
        )
