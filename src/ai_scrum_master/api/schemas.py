from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateStoriesRequest(BaseModel):
    requirement: str = Field(..., min_length=3)
    n_results: int = Field(default=5, ge=1, le=10)


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
    warnings: list[str] = Field(default_factory=list)


class StoryDraft(BaseModel):
    title: str
    user_story: str
    acceptance_criteria: list[str]
    story_points: int
    tasks: dict[str, list[str]]
    definition_of_done: list[str]
    planning_status: str = "READY"
    clarification_questions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    story_splits: list[dict] = Field(default_factory=list)
    sprint_allocation: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    status: str
    issues: list[str] = Field(default_factory=list)
    revision_instructions: list[str] = Field(default_factory=list)
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
    story: StoryDraft
    evaluation: EvaluationResult
    actions: ActionPlan
