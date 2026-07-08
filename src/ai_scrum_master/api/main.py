from __future__ import annotations

import threading
import uuid
from pathlib import Path
import tempfile
import shutil

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from ai_scrum_master.actions.jira import JiraTool
from ai_scrum_master.actions.slack import SlackTool
from ai_scrum_master.api.responses import build_envelope_response
from ai_scrum_master.api.routers.generate import router as generate_router
from ai_scrum_master.api.schemas import (
    ApiResponseEnvelope,
    ActionExecutionPlan,
    ActionExecutionResult,
    ActionPlan,
    ActionPreviewRequest,
    IngestJobResponse,
    IngestRequest,
    IngestResponse,
    IngestStatusResponse,
)
from ai_scrum_master.core.config.settings import get_settings
from ai_scrum_master.core.utils.exceptions import BaseAppException
from ai_scrum_master.core.pipeline.finalizer import ACTION_BLOCK_WARNING, actions_are_ready
from ai_scrum_master.core.utils.logging import get_logger
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
from ai_scrum_master.api.routers.dashboard import router as dashboard_router

logger = get_logger(__name__)
app.include_router(generate_router)
app.include_router(history_router)
app.include_router(projects_router)
app.include_router(sprint_router)
app.include_router(dashboard_router)

from ai_scrum_master.worker.tasks import ingest_docs_task
from celery.result import AsyncResult

def get_ingest_runner():
    from ai_scrum_master.ingestion.ingest import ingest_raw_docs
    return ingest_raw_docs

@app.get("/health", response_model=ApiResponseEnvelope)
def health() -> ApiResponseEnvelope:
    return build_envelope_response(
        endpoint="health",
        data={"status": "ok"},
    )


@app.post("/ingest", response_model=ApiResponseEnvelope)
def ingest_documents(
    payload: IngestRequest,
    ingest_runner=Depends(get_ingest_runner),
) -> ApiResponseEnvelope:
    result = ingest_runner(
        raw_docs_dir=Path(payload.raw_docs_dir) if payload.raw_docs_dir else None,
        project_id=payload.project_id
    )
    return build_envelope_response(
        endpoint="ingest_create",
        project_id=payload.project_id,
        data=IngestResponse(**result).model_dump(),
    )


@app.post("/ingest/upload", response_model=ApiResponseEnvelope)
def ingest_uploaded_documents(
    project_id: str | None = None,
    files: list[UploadFile] = File(...),
) -> ApiResponseEnvelope:
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

    return build_envelope_response(
        endpoint="ingest_upload",
        project_id=project_id,
        data=IngestJobResponse(
            job_id=task.id,
            status="processing",
            message=f"Started ingesting {len(saved_files)} file(s) in background",
        ).model_dump(),
    )


from ai_scrum_master.worker.celery_app import celery_app

@app.get("/ingest/status/{job_id}", response_model=ApiResponseEnvelope)
def get_ingest_status(job_id: str) -> ApiResponseEnvelope:
    """Poll ingestion job status."""
    task_result = AsyncResult(job_id, app=celery_app)
    
    if task_result.state == 'SUCCESS':
        raw_result = task_result.result
        result_data = IngestResponse(**{
            k: v for k, v in raw_result.items()
            if k in ("collection", "source_dir", "files_indexed", "chunks_indexed", "skipped_count", "indexed_files", "skipped_files")
        }) if raw_result else None
        
        payload = IngestStatusResponse(
            job_id=job_id,
            status="completed",
            message="Job completed successfully.",
            result=result_data,
        )
    elif task_result.state == 'FAILURE':
        payload = IngestStatusResponse(
            job_id=job_id,
            status="failed",
            message=str(task_result.info),
            result=None,
        )
    else:
        # PENDING, STARTED, RETRY, RECEIVED, etc.
        payload = IngestStatusResponse(
            job_id=job_id,
            status="processing",
            message=f"Job is {task_result.state.lower()}...",
            result=None,
        )
    return build_envelope_response(
        endpoint="ingest_status",
        project_id=None,
        data=payload.model_dump(),
    )


@app.post("/actions/jira/preview", response_model=ApiResponseEnvelope)
def preview_jira_action(
    payload: ActionPreviewRequest,
) -> ApiResponseEnvelope:
    story = payload.story.model_dump()
    evaluation = payload.evaluation.model_dump()
    if not actions_are_ready(story, evaluation):
        action_plan = ActionPlan(
            jira={"ready": False, "payload": None, "warnings": [_action_block_warning()]},
            slack={"ready": False, "payload": None, "warnings": ["Slack preview is not part of this endpoint."]},
        )
        return build_envelope_response(
            endpoint="actions_jira_preview",
            project_id=payload.project_id,
            data=action_plan.model_dump(),
        )

    jira_tool = JiraTool.from_project(payload.project_id)
    action_plan = ActionPlan(
        jira=jira_tool.prepare_action(story),
        slack={"ready": False, "payload": None, "warnings": ["Slack preview is not part of this endpoint."]},
    )
    return build_envelope_response(
        endpoint="actions_jira_preview",
        project_id=payload.project_id,
        data=action_plan.model_dump(),
    )


@app.post("/actions/slack/preview", response_model=ApiResponseEnvelope)
def preview_slack_action(
    payload: ActionPreviewRequest,
) -> ApiResponseEnvelope:
    story = payload.story.model_dump()
    evaluation = payload.evaluation.model_dump()
    if not actions_are_ready(story, evaluation):
        action_plan = ActionPlan(
            jira={"ready": False, "payload": None, "warnings": ["Jira preview is not part of this endpoint."]},
            slack={"ready": False, "payload": None, "warnings": [_action_block_warning()]},
        )
        return build_envelope_response(
            endpoint="actions_slack_preview",
            project_id=payload.project_id,
            data=action_plan.model_dump(),
        )

    slack_tool = SlackTool.from_project(payload.project_id)
    action_plan = ActionPlan(
        jira={"ready": False, "payload": None, "warnings": ["Jira preview is not part of this endpoint."]},
        slack=slack_tool.prepare_action(story, evaluation),
    )
    return build_envelope_response(
        endpoint="actions_slack_preview",
        project_id=payload.project_id,
        data=action_plan.model_dump(),
    )


@app.post("/actions/jira/execute", response_model=ApiResponseEnvelope)
def execute_jira_action(
    payload: ActionPreviewRequest,
) -> ApiResponseEnvelope:
    story = payload.story.model_dump()
    evaluation = payload.evaluation.model_dump()
    logger.info("Jira execute endpoint entered evaluation_status=%s", evaluation["status"])
    if not actions_are_ready(story, evaluation):
        execution_plan = ActionExecutionPlan(
            jira=_blocked_execution(_action_block_warning()),
            slack=_not_part_of_execution("Slack execution is not part of this endpoint."),
        )
        return build_envelope_response(
            endpoint="actions_jira_execute",
            project_id=payload.project_id,
            data=execution_plan.model_dump(),
        )

    jira_tool = JiraTool.from_project(payload.project_id)
    if not jira_tool.config.is_configured:
        raise HTTPException(status_code=400, detail="Jira configuration is missing for this project. Please configure Jira in Settings first.")

    execution_plan = ActionExecutionPlan(
        jira=jira_tool.execute_action(story),
        slack=_not_part_of_execution("Slack execution is not part of this endpoint."),
    )
    return build_envelope_response(
        endpoint="actions_jira_execute",
        project_id=payload.project_id,
        data=execution_plan.model_dump(),
    )


@app.post("/actions/slack/execute", response_model=ApiResponseEnvelope)
def execute_slack_action(
    payload: ActionPreviewRequest,
) -> ApiResponseEnvelope:
    story = payload.story.model_dump()
    evaluation = payload.evaluation.model_dump()
    logger.info("Slack execute endpoint entered evaluation_status=%s", evaluation["status"])
    if not actions_are_ready(story, evaluation):
        execution_plan = ActionExecutionPlan(
            jira=_not_part_of_execution("Jira execution is not part of this endpoint."),
            slack=_blocked_execution(_action_block_warning()),
        )
        return build_envelope_response(
            endpoint="actions_slack_execute",
            project_id=payload.project_id,
            data=execution_plan.model_dump(),
        )

    slack_tool = SlackTool.from_project(payload.project_id)
    execution_plan = ActionExecutionPlan(
        jira=_not_part_of_execution("Jira execution is not part of this endpoint."),
        slack=slack_tool.execute_action(story, evaluation),
    )
    return build_envelope_response(
        endpoint="actions_slack_execute",
        project_id=payload.project_id,
        data=execution_plan.model_dump(),
    )


@app.post("/actions/execute-all", response_model=ApiResponseEnvelope)
def execute_all_actions(
    payload: ActionPreviewRequest,
) -> ApiResponseEnvelope:
    story = payload.story.model_dump()
    evaluation = payload.evaluation.model_dump()
    logger.info("Execute-all endpoint entered evaluation_status=%s", evaluation["status"])
    if not actions_are_ready(story, evaluation):
        blocked = _blocked_execution(_action_block_warning())
        execution_plan = ActionExecutionPlan(jira=blocked, slack=blocked)
        return build_envelope_response(
            endpoint="actions_execute_all",
            project_id=payload.project_id,
            data=execution_plan.model_dump(),
        )

    jira_tool = JiraTool.from_project(payload.project_id)
    if not jira_tool.config.is_configured:
        raise HTTPException(status_code=400, detail="Jira configuration is missing for this project. Please configure Jira in Settings first.")

    # Execute Jira first so we can include the Jira link in the Slack message
    jira_result = jira_tool.execute_action(story)
    
    # Execute GitHub if configured and Jira was successful
    github_result = None
    from ai_scrum_master.actions.github import GithubTool
    github_tool = GithubTool.from_project(payload.project_id)
    if github_tool.config.is_configured and jira_result.get("executed"):
        story_key = jira_result.get("created", {}).get("story_key")
        if story_key:
            import re
            title = story.get("title", "")
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
            
            req_type = story.get("story_type", "feature")
            prefix = "bugfix" if req_type == "bug_report" else "feature"
            
            branch_name = f"{prefix}/{story_key}-{slug}"
            if len(branch_name) > 60:
                branch_name = branch_name[:60].rstrip('-')
                
            gh_res = github_tool.create_feature_branch(branch_name)
            github_result = ActionExecutionResult(
                ready=True,
                executed=gh_res.get("ready", False),
                payload={"branch_name": branch_name},
                created={"branch_url": gh_res.get("branch_url")} if gh_res.get("ready") else {},
                failed=[] if gh_res.get("ready") else [{"error": "Failed to create branch"}],
                warnings=gh_res.get("warnings", [])
            )
    
    slack_tool = SlackTool.from_project(payload.project_id)
    slack_result = slack_tool.execute_action(story, evaluation, jira_created=jira_result.get("created"))

    execution_plan = ActionExecutionPlan(
        jira=jira_result,
        slack=slack_result,
        github=github_result,
    )
    return build_envelope_response(
        endpoint="actions_execute_all",
        project_id=payload.project_id,
        data=execution_plan.model_dump(),
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
