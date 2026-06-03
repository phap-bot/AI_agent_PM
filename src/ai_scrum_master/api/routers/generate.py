from __future__ import annotations

from fastapi import APIRouter, Depends

from ai_scrum_master.api.schemas import GenerateStoriesRequest, GenerateStoriesResponse
from ai_scrum_master.core.pipeline import ScrumMasterCrew, generate_story_pipeline

router = APIRouter()


def get_crew() -> ScrumMasterCrew:
    return ScrumMasterCrew()


import threading
import uuid
from fastapi import HTTPException
from ai_scrum_master.api.schemas import GenerateJobResponse, GenerateStatusResponse

_generate_jobs: dict[str, dict] = {}

def _run_generate_job(job_id: str, requirement: str, n_results: int, allow_fallback_without_context: bool, crew: ScrumMasterCrew):
    try:
        def progress_callback(stage: str, partial_data: dict):
            _generate_jobs[job_id]["stage"] = stage
            _generate_jobs[job_id]["partial_result"].update(partial_data)

        result = generate_story_pipeline(
            requirement=requirement,
            n_results=n_results,
            allow_fallback_without_context=allow_fallback_without_context,
            crew=crew,
            progress_callback=progress_callback
        )
        _generate_jobs[job_id]["status"] = "completed"
        _generate_jobs[job_id]["stage"] = "completed"
        _generate_jobs[job_id]["result"] = GenerateStoriesResponse(**result)
    except Exception as e:
        _generate_jobs[job_id]["status"] = "failed"
        _generate_jobs[job_id]["message"] = str(e)


@router.post("/generate", response_model=GenerateJobResponse)
def generate_stories(
    payload: GenerateStoriesRequest,
    crew: ScrumMasterCrew = Depends(get_crew),
) -> GenerateJobResponse:
    job_id = str(uuid.uuid4())
    _generate_jobs[job_id] = {
        "status": "processing",
        "stage": "researcher",
        "message": "",
        "partial_result": {},
        "result": None,
    }
    
    thread = threading.Thread(
        target=_run_generate_job,
        args=(job_id, payload.requirement, payload.n_results, payload.allow_fallback_without_context, crew)
    )
    thread.daemon = True
    thread.start()
    
    return GenerateJobResponse(job_id=job_id)


@router.get("/generate/status/{job_id}", response_model=GenerateStatusResponse)
def get_generate_status(job_id: str) -> GenerateStatusResponse:
    job = _generate_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return GenerateStatusResponse(
        job_id=job_id,
        status=job["status"],
        stage=job["stage"],
        message=job["message"],
        partial_result=job["partial_result"],
        result=job["result"]
    )
