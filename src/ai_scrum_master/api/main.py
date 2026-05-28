from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI

from ai_scrum_master.actions.jira import JiraTool
from ai_scrum_master.actions.slack import SlackTool
from ai_scrum_master.api.routers.generate import generate_stories, get_crew, router as generate_router
from ai_scrum_master.api.schemas import (
    ActionExecutionPlan,
    ActionExecutionResult,
    ActionPlan,
    ActionPreviewRequest,
    IngestRequest,
    IngestResponse,
)
from ai_scrum_master.core.config import get_settings
from ai_scrum_master.core.finalizer import ACTION_BLOCK_WARNING, actions_are_ready
from ai_scrum_master.core.logging import get_logger
from ai_scrum_master.ingestion.ingest import ingest_raw_docs

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)
logger = get_logger(__name__)
app.include_router(generate_router)


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
        collection_name=payload.collection_name,
    )
    return IngestResponse(**result)


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

    return ActionExecutionPlan(
        jira=jira_tool.execute_action(story),
        slack=slack_tool.execute_action(story, evaluation),
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
