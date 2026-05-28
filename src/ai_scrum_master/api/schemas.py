from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateStoriesRequest(BaseModel):
    requirement: str = Field(..., min_length=3)
    n_results: int = Field(default=5, ge=1, le=10)
    allow_fallback_without_context: bool = False


class IngestRequest(BaseModel):
    raw_docs_dir: str | None = None
    collection_name: str | None = None


class IngestResponse(BaseModel):
    collection: str
    source_dir: str
    files_indexed: int
    chunks_indexed: int


class ResearchContext(BaseModel):
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
    warnings: list[str] = Field(default_factory=list)


class StoryDraft(BaseModel):
    title: str
    requirement: str = ""
    story_type: str = "software_feature"
    user_story: str
    acceptance_criteria: list[str]
    story_points: int | None = None
    tasks: dict[str, list[str]]
    definition_of_done: list[str]
    planning_status: str = "READY"
    clarification_questions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    story_splits: list[dict] = Field(default_factory=list)
    sprint_allocation: list[dict] = Field(default_factory=list)
    context_sources: list[dict] = Field(default_factory=list)
    context_quality: dict = Field(default_factory=dict)
    planner_quality: dict = Field(default_factory=dict)
    route: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    status: str
    issues: list[str] = Field(default_factory=list)
    revision_instructions: list[str] = Field(default_factory=list)
    dod_score: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class PreparedAction(BaseModel):
    ready: bool
    payload: dict | str | None = None
    subtasks: list[dict] | str | None = None
    warnings: list[str] = Field(default_factory=list)


class ActionPlan(BaseModel):
    jira: PreparedAction
    slack: PreparedAction


class ActionExecutionResult(BaseModel):
    ready: bool
    executed: bool
    payload: dict | str | None = None
    created: dict | list | None = None
    failed: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    status_code: int | None = None


class ActionExecutionPlan(BaseModel):
    jira: ActionExecutionResult
    slack: ActionExecutionResult


class ActionPreviewRequest(BaseModel):
    story: StoryDraft
    evaluation: EvaluationResult = Field(default_factory=lambda: EvaluationResult(status="APPROVED"))


class GenerateStoriesResponse(BaseModel):
    context: ResearchContext
    story: StoryDraft | None = None
    evaluation: EvaluationResult
    actions: ActionPlan
    next_steps: list[str] = Field(default_factory=list)
