from __future__ import annotations

import threading
import uuid
from pathlib import Path
import tempfile
import shutil

from fastapi import Depends, FastAPI, File, UploadFile
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

logger = get_logger(__name__)
app.include_router(generate_router)

# ---------------------------------------------------------------------------
# In-memory job tracker for async ingestion
# ---------------------------------------------------------------------------
_ingest_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def _run_ingest_job(job_id: str, source_dir: Path):
    """Run ingestion in a background thread and update the job tracker."""
    logger.info("[JOB %s] Background ingestion started for %s", job_id, source_dir)
    try:
        result = ingest_raw_docs(raw_docs_dir=source_dir)
        with _jobs_lock:
            _ingest_jobs[job_id] = {
                "status": "completed",
                "message": f"Ingested {result['files_indexed']} files / {result['chunks_indexed']} chunks",
                "result": result,
            }
        logger.info("[JOB %s] Ingestion completed: %s", job_id, result)
    except Exception as exc:
        logger.exception("[JOB %s] Ingestion FAILED: %s", job_id, exc)
        with _jobs_lock:
            _ingest_jobs[job_id] = {
                "status": "failed",
                "message": str(exc),
                "result": None,
            }
    finally:
        # Clean up temp directory if it exists
        if source_dir and source_dir.exists() and "tmp" in str(source_dir).lower():
            shutil.rmtree(source_dir, ignore_errors=True)
            logger.info("[JOB %s] Cleaned up temp dir %s", job_id, source_dir)


# ---------------------------------------------------------------------------


def get_jira_tool() -> JiraTool:
    return JiraTool()


def get_slack_tool() -> SlackTool:
    return SlackTool()


def get_ingest_runner():
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
    )
    return IngestResponse(**result)


@app.post("/ingest/upload", response_model=IngestJobResponse)
def ingest_uploaded_documents(
    files: list[UploadFile] = File(...),
) -> IngestJobResponse:
    """Accept uploaded files and start ingestion in the background.
    Returns immediately with a job_id for polling status."""
    job_id = str(uuid.uuid4())[:8]

    # Save uploaded files to a temp directory
    temp_dir = Path(tempfile.mkdtemp())
    saved_files = []
    for file in files:
        file_path = temp_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)

    logger.info("[JOB %s] Received %d files: %s -> temp_dir=%s", job_id, len(saved_files), saved_files, temp_dir)

    # Register job as processing
    with _jobs_lock:
        _ingest_jobs[job_id] = {
            "status": "processing",
            "message": f"Processing {len(saved_files)} file(s)...",
            "result": None,
        }

    # Start background thread
    thread = threading.Thread(target=_run_ingest_job, args=(job_id, temp_dir), daemon=True)
    thread.start()

    return IngestJobResponse(
        job_id=job_id,
        status="processing",
        message=f"Started ingesting {len(saved_files)} file(s) in background",
    )


@app.get("/ingest/status/{job_id}", response_model=IngestStatusResponse)
def get_ingest_status(job_id: str) -> IngestStatusResponse:
    """Poll ingestion job status."""
    with _jobs_lock:
        job = _ingest_jobs.get(job_id)

    if job is None:
        return IngestStatusResponse(
            job_id=job_id,
            status="not_found",
            message=f"No job with id '{job_id}' found.",
        )

    result_data = None
    if job.get("result"):
        result_data = IngestResponse(**{
            k: v for k, v in job["result"].items()
            if k in ("collection", "source_dir", "files_indexed", "chunks_indexed", "skipped_count", "indexed_files", "skipped_files")
        })

    return IngestStatusResponse(
        job_id=job_id,
        status=job["status"],
        message=job.get("message", ""),
        result=result_data,
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
