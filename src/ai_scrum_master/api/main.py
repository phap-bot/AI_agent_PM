from __future__ import annotations

import threading
import uuid
from pathlib import Path
import tempfile
import shutil

from fastapi import Depends, FastAPI, File, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from ai_scrum_master.actions.jira import JiraTool
from ai_scrum_master.actions.slack import SlackTool
from ai_scrum_master.api.routers.generate import generate_stories, get_crew, router as generate_router
from ai_scrum_master.api.schemas import (
    ActionExecutionPlan,
    ActionExecutionResult,
    ActionPlan,
    ActionPreviewRequest,
    IngestJobResponse,
    IngestRequest,
    IngestResponse,
    IngestStatusResponse,
)
from ai_scrum_master.core.config import get_settings
from ai_scrum_master.core.exceptions import BaseAppException
from ai_scrum_master.core.finalizer import ACTION_BLOCK_WARNING, actions_are_ready
from ai_scrum_master.core.logging import get_logger
from ai_scrum_master.ingestion.ingest import ingest_raw_docs

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Fallback for unexpected errors
    logger.exception(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Đã xảy ra lỗi không xác định từ hệ thống.",
                "details": str(exc)
            }
        }
    )

import logging

class EndpointFilter(logging.Filter):
    def __init__(self, path: str):
        super().__init__()
        self.path = path

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            # record.args[2] usually contains the request path in uvicorn access logs
            return self.path not in record.args[2]
        except (IndexError, TypeError):
            return True

# Filter out status polling spam from logs
logging.getLogger("uvicorn.access").addFilter(EndpointFilter("/generate/status/"))
logging.getLogger("uvicorn.access").addFilter(EndpointFilter("/ingest/status/"))

from ai_scrum_master.api.routers.history import router as history_router
from ai_scrum_master.api.routers.projects import router as projects_router
from ai_scrum_master.api.routers.sprint import router as sprint_router

logger = get_logger(__name__)
app.include_router(generate_router)
app.include_router(history_router)
app.include_router(projects_router)
app.include_router(sprint_router)

from ai_scrum_master.worker.tasks import ingest_docs_task
from celery.result import AsyncResult

def get_jira_tool() -> JiraTool:
    return JiraTool()

def get_slack_tool() -> SlackTool:
    return SlackTool()

def get_ingest_runner():
    from ai_scrum_master.ingestion.ingest import ingest_raw_docs
    return ingest_raw_docs

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
def ingest_documents(
    payload: IngestRequest,
    ingest_runner=Depends(get_ingest_runner),
) -> IngestResponse:
    result = ingest_runner(
        raw_docs_dir=Path(payload.raw_docs_dir) if payload.raw_docs_dir else None,
        project_id=payload.project_id
    )
    return IngestResponse(**result)


@app.post("/ingest/upload", response_model=IngestJobResponse)
def ingest_uploaded_documents(
    project_id: str | None = None,
    files: list[UploadFile] = File(...),
) -> IngestJobResponse:
    """Accept uploaded files and start ingestion in the background using Celery.
    Returns immediately with a job_id for polling status."""

    # Save uploaded files to a temp directory
    temp_dir = Path(tempfile.mkdtemp())
    saved_files = []
    for file in files:
        file_path = temp_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)

    logger.info("Received %d files: %s -> temp_dir=%s", len(saved_files), saved_files, temp_dir)

    # Start Celery task
    task = ingest_docs_task.delay(str(temp_dir), project_id)

    return IngestJobResponse(
        job_id=task.id,
        status="processing",
        message=f"Started ingesting {len(saved_files)} file(s) in background",
    )


@app.get("/ingest/status/{job_id}", response_model=IngestStatusResponse)
def get_ingest_status(job_id: str) -> IngestStatusResponse:
    """Poll ingestion job status."""
    task_result = AsyncResult(job_id)
    
    if task_result.state == 'PENDING':
        return IngestStatusResponse(
            job_id=job_id,
            status="processing",
            message="Job is pending...",
            result=None,
        )
    elif task_result.state == 'PROCESSING':
        return IngestStatusResponse(
            job_id=job_id,
            status="processing",
            message="Job is processing...",
            result=None,
        )
    elif task_result.state == 'SUCCESS':
        raw_result = task_result.result
        result_data = IngestResponse(**{
            k: v for k, v in raw_result.items()
            if k in ("collection", "source_dir", "files_indexed", "chunks_indexed", "skipped_count", "indexed_files", "skipped_files")
        }) if raw_result else None
        
        return IngestStatusResponse(
            job_id=job_id,
            status="completed",
            message="Job completed successfully.",
            result=result_data,
        )
    elif task_result.state == 'FAILURE':
        return IngestStatusResponse(
            job_id=job_id,
            status="failed",
            message=str(task_result.info),
            result=None,
        )
    else:
        return IngestStatusResponse(
            job_id=job_id,
            status="failed",
            message=f"Unknown task state: {task_result.state}",
            result=None,
        )


@app.post("/actions/jira/preview", response_model=ActionPlan)
def preview_jira_action(
    payload: ActionPreviewRequest,
    jira_tool: JiraTool = Depends(get_jira_tool),
) -> ActionPlan:
    story = payload.story.model_dump()
    evaluation = payload.evaluation.model_dump()
    if not actions_are_ready(story, evaluation):
        return ActionPlan(
            jira={"ready": False, "payload": None, "warnings": [_action_block_warning()]},
            slack={"ready": False, "payload": None, "warnings": ["Slack preview is not part of this endpoint."]},
        )

    return ActionPlan(
        jira=jira_tool.prepare_action(story),
        slack={"ready": False, "payload": None, "warnings": ["Slack preview is not part of this endpoint."]},
    )


@app.post("/actions/slack/preview", response_model=ActionPlan)
def preview_slack_action(
    payload: ActionPreviewRequest,
    slack_tool: SlackTool = Depends(get_slack_tool),
) -> ActionPlan:
    story = payload.story.model_dump()
    evaluation = payload.evaluation.model_dump()
    if not actions_are_ready(story, evaluation):
        return ActionPlan(
            jira={"ready": False, "payload": None, "warnings": ["Jira preview is not part of this endpoint."]},
            slack={"ready": False, "payload": None, "warnings": [_action_block_warning()]},
        )

    return ActionPlan(
        jira={"ready": False, "payload": None, "warnings": ["Jira preview is not part of this endpoint."]},
        slack=slack_tool.prepare_action(story, evaluation),
    )


@app.post("/actions/jira/execute", response_model=ActionExecutionPlan)
def execute_jira_action(
    payload: ActionPreviewRequest,
    jira_tool: JiraTool = Depends(get_jira_tool),
) -> ActionExecutionPlan:
    story = payload.story.model_dump()
    evaluation = payload.evaluation.model_dump()
    logger.info("Jira execute endpoint entered evaluation_status=%s", evaluation["status"])
    if not actions_are_ready(story, evaluation):
        return ActionExecutionPlan(
            jira=_blocked_execution(_action_block_warning()),
            slack=_not_part_of_execution("Slack execution is not part of this endpoint."),
        )

    return ActionExecutionPlan(
        jira=jira_tool.execute_action(story),
        slack=_not_part_of_execution("Slack execution is not part of this endpoint."),
    )


@app.post("/actions/slack/execute", response_model=ActionExecutionPlan)
def execute_slack_action(
    payload: ActionPreviewRequest,
    slack_tool: SlackTool = Depends(get_slack_tool),
) -> ActionExecutionPlan:
    story = payload.story.model_dump()
    evaluation = payload.evaluation.model_dump()
    logger.info("Slack execute endpoint entered evaluation_status=%s", evaluation["status"])
    if not actions_are_ready(story, evaluation):
        return ActionExecutionPlan(
            jira=_not_part_of_execution("Jira execution is not part of this endpoint."),
            slack=_blocked_execution(_action_block_warning()),
        )

    return ActionExecutionPlan(
        jira=_not_part_of_execution("Jira execution is not part of this endpoint."),
        slack=slack_tool.execute_action(story, evaluation),
    )


@app.post("/actions/execute-all", response_model=ActionExecutionPlan)
def execute_all_actions(
    payload: ActionPreviewRequest,
    jira_tool: JiraTool = Depends(get_jira_tool),
    slack_tool: SlackTool = Depends(get_slack_tool),
) -> ActionExecutionPlan:
    story = payload.story.model_dump()
    evaluation = payload.evaluation.model_dump()
    logger.info("Execute-all endpoint entered evaluation_status=%s", evaluation["status"])
    if not actions_are_ready(story, evaluation):
        blocked = _blocked_execution(_action_block_warning())
        return ActionExecutionPlan(jira=blocked, slack=blocked)

    # Execute Jira first so we can include the Jira link in the Slack message
    jira_result = jira_tool.execute_action(story)
    
    # Pass the Jira 'created' result to Slack execution
    slack_result = slack_tool.execute_action(story, evaluation, jira_created=jira_result.get("created"))

    return ActionExecutionPlan(
        jira=jira_result,
        slack=slack_result,
    )


def _action_block_warning() -> str:
    return ACTION_BLOCK_WARNING


def _blocked_execution(warning: str) -> ActionExecutionResult:
    logger.info("Action execution blocked: %s", warning)
    return ActionExecutionResult(
        ready=False,
        executed=False,
        payload=None,
        created={},
        failed=[],
        warnings=[warning],
        status_code=None,
    )


def _not_part_of_execution(warning: str) -> ActionExecutionResult:
    return ActionExecutionResult(
        ready=False,
        executed=False,
        payload=None,
        created={},
        failed=[],
        warnings=[warning],
        status_code=None,
    )
