from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

MARKDOWN_FENCE_RE = re.compile(r"^\s*(?:```|''')\s*(?:json|markdown|md)?\s*|\s*(?:```|''')\s*$", re.IGNORECASE)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
MARKDOWN_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
MARKDOWN_FORMAT_RE = re.compile(r"(?<!\\)([*`~]{1,3})(.*?)(?<!\\)\1")
HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"[ \t]+")


def sanitize_markdown(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    text = MARKDOWN_FENCE_RE.sub("", text).strip()
    text = MARKDOWN_IMAGE_RE.sub(r"\1", text)
    text = MARKDOWN_LINK_RE.sub(r"\1", text)
    text = HTML_TAG_RE.sub("", text)
    previous = None
    while previous != text:
        previous = text
        text = MARKDOWN_FORMAT_RE.sub(r"\2", text)
    text = "\n".join(WHITESPACE_RE.sub(" ", line).strip() for line in text.splitlines())
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def sanitize_markdown_deep(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_markdown(value)
    if isinstance(value, list):
        return [sanitize_markdown_deep(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_markdown_deep(item) for key, item in value.items()}
    return value


class SanitizedBaseModel(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    @model_validator(mode="before")
    @classmethod
    def sanitize_markdown_fields(cls, data: Any) -> Any:
        return sanitize_markdown_deep(data)


class GenerateStoriesRequest(SanitizedBaseModel):
    requirement: str = Field(..., min_length=3)
    n_results: int = Field(default=5, ge=1, le=10)
    allow_fallback_without_context: bool = False
    forced_context_docs: list[str] = Field(default_factory=list)
    project_id: str | None = None


class IngestRequest(SanitizedBaseModel):
    raw_docs_dir: str | None = None
    project_id: str | None = None


class IngestResponse(SanitizedBaseModel):
    collection: str
    source_dir: str
    files_indexed: int
    chunks_indexed: int
    skipped_count: int = 0
    indexed_files: list[str] = Field(default_factory=list)
    skipped_files: list[str] = Field(default_factory=list)


class IngestJobResponse(SanitizedBaseModel):
    job_id: str
    status: str = "processing"  # processing | completed | failed
    message: str = "Ingestion started in background"


class IngestStatusResponse(SanitizedBaseModel):
    job_id: str
    status: str = "processing"  # processing | completed | failed
    message: str = ""
    result: IngestResponse | None = None


class GenerateJobResponse(SanitizedBaseModel):
    job_id: str
    status: str = "processing"
    message: str = "Generation started in background"


class GenerateStatusResponse(SanitizedBaseModel):
    job_id: str
    status: str = "processing"
    stage: str = "researcher"  # researcher | planner | evaluator | completed
    message: str = ""
    partial_result: dict = Field(default_factory=dict)
    result: Any | None = None


class ResearchContext(SanitizedBaseModel):
    documents: list[str] = Field(default_factory=list)
    ids: list[str] = Field(default_factory=list)
    metadatas: list[dict] = Field(default_factory=list)
    distances: list[float | None] = Field(default_factory=list)
    matches: list[dict] = Field(default_factory=list)
    retrieved_sources: list[dict] = Field(default_factory=list)
    selected_context_sources: list[dict] = Field(default_factory=list)
    ignored_context_sources: list[dict] = Field(default_factory=list)
    context_snippets: list[str] = Field(default_factory=list)
    planning_brief: dict = Field(default_factory=dict)
    retrieval_status: str = "empty"
    retrieval_threshold: float = 0.0
    raw_match_count: int = 0
    confidence: float = 0.0
    quality_gate: dict = Field(default_factory=dict)
    route: dict = Field(default_factory=dict)
    required_sources: list[str] = Field(default_factory=list)
    optional_sources: list[str] = Field(default_factory=list)
    missing_required_sources: list[str] = Field(default_factory=list)
    missing_optional_sources: list[str] = Field(default_factory=list)
    latency_ms: int = 0
    stage_latencies_ms: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class StoryDraft(SanitizedBaseModel):
    title: str = ""
    requirement: str = ""
    story_type: str = ""
    user_story: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    story_points: StrictInt | None = None
    priority: str | None = None
    tasks: dict[str, list[str]] = Field(default_factory=lambda: {"be": [], "fe": [], "qa": []})
    definition_of_done: list[str] = Field(default_factory=list)
    planning_status: str = "READY"
    clarification_questions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    story_splits: list[dict] = Field(default_factory=list)
    sprint_allocation: list[dict] = Field(default_factory=list)
    context_sources: list[dict] = Field(default_factory=list)
    context_quality: dict = Field(default_factory=dict)
    planner_quality: dict = Field(default_factory=dict)
    route: dict = Field(default_factory=dict)
    latency_ms: int = 0
    stage_latencies_ms: dict[str, int] = Field(default_factory=dict)
    repair_attempts_used: int = 0
    timed_out: bool = False
    failure_type: str = ""
    warnings: list[str] = Field(default_factory=list)


class EvaluationResult(SanitizedBaseModel):
    status: str = "REVISION"
    issues: list[str] = Field(default_factory=list)
    revision_instructions: list[str] = Field(default_factory=list)
    dod_score: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class PreparedAction(SanitizedBaseModel):
    ready: bool
    payload: dict | str | None = None
    subtasks: list[dict] | str | None = None
    warnings: list[str] = Field(default_factory=list)


class ActionPlan(SanitizedBaseModel):
    jira: PreparedAction
    slack: PreparedAction
    github: PreparedAction | None = None


class ActionExecutionResult(SanitizedBaseModel):
    ready: bool
    executed: bool
    payload: dict | str | None = None
    created: dict | list | None = None
    failed: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    status_code: int | None = None


class ActionExecutionPlan(SanitizedBaseModel):
    jira: ActionExecutionResult
    slack: ActionExecutionResult
    github: ActionExecutionResult | None = None


class ActionPreviewRequest(SanitizedBaseModel):
    story: StoryDraft = Field(default_factory=StoryDraft)
    evaluation: EvaluationResult = Field(default_factory=lambda: EvaluationResult(status="APPROVED"))
    project_id: str | None = None


class GenerateStoriesResponse(SanitizedBaseModel):
    context: ResearchContext = Field(default_factory=ResearchContext)
    story: StoryDraft | None = None
    evaluation: EvaluationResult = Field(default_factory=EvaluationResult)
    actions: ActionPlan = Field(default_factory=lambda: ActionPlan(jira=PreparedAction(ready=False), slack=PreparedAction(ready=False)))
    next_steps: list[str] = Field(default_factory=list)
