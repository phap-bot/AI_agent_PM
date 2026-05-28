from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ContextSourceOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = ""
    source: str = "unknown source"
    chunk_index: str | int = "?"
    score: float = 0.0
    distance: Any = None
    excerpt: str = ""


class EvidenceOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    evidence_id: str
    source: str = "unknown source"
    chunk_index: str | int = "?"
    score: float = 0.0
    excerpt: str = ""


class PlanningBriefOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    requirement: str = ""
    retrieval_status: str = "empty"
    confidence: float = 0.0
    source_count: int = 0
    usable_evidence: list[EvidenceOutput] = Field(default_factory=list)
    planning_instruction: str = ""


class ResearchContextOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    documents: list[str] = Field(default_factory=list)
    ids: list[str] = Field(default_factory=list)
    metadatas: list[dict[str, Any]] = Field(default_factory=list)
    distances: list[float | None] = Field(default_factory=list)
    matches: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_sources: list[ContextSourceOutput] = Field(default_factory=list)
    selected_context_sources: list[ContextSourceOutput] = Field(default_factory=list)
    ignored_context_sources: list[ContextSourceOutput] = Field(default_factory=list)
    context_snippets: list[str] = Field(default_factory=list)
    planning_brief: PlanningBriefOutput = Field(default_factory=PlanningBriefOutput)
    retrieval_status: str = "empty"
    retrieval_threshold: float = 0.0
    raw_match_count: int = 0
    confidence: float = 0.0
    quality_gate: dict[str, Any] = Field(default_factory=dict)
    route: dict[str, Any] = Field(default_factory=dict)
    required_sources: list[str] = Field(default_factory=list)
    optional_sources: list[str] = Field(default_factory=list)
    missing_required_sources: list[str] = Field(default_factory=list)
    missing_optional_sources: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class StoryTasksOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    be: list[str] = Field(default_factory=list)
    fe: list[str] = Field(default_factory=list)
    qa: list[str] = Field(default_factory=list)


class StorySplitOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = ""
    user_story: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    story_points: int | None = None
    tasks: StoryTasksOutput = Field(default_factory=StoryTasksOutput)
    definition_of_done: list[str] = Field(default_factory=list)


class PlannerStoryOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str
    story_type: Literal["software_feature", "process_improvement", "oversized_request", "ambiguous_request"] = "software_feature"
    user_story: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    story_points: int | None = None
    tasks: StoryTasksOutput = Field(default_factory=StoryTasksOutput)
    definition_of_done: list[str] = Field(default_factory=list)
    planning_status: Literal["READY", "NEEDS_CLARIFICATION", "NEEDS_SPLIT", "SPLIT_RECOMMENDED", "REVISION"] = "REVISION"
    clarification_questions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    story_splits: list[StorySplitOutput] = Field(default_factory=list)
    sprint_allocation: list[dict[str, Any]] = Field(default_factory=list)
    context_sources: list[ContextSourceOutput] = Field(default_factory=list)
    context_quality: dict[str, Any] = Field(default_factory=dict)
    route: dict[str, Any] = Field(default_factory=dict)
    fallback_used: bool = False
    warnings: list[str] = Field(default_factory=list)


class EvaluationOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["APPROVED", "REVISION"]
    issues: list[str] = Field(default_factory=list)
    revision_instructions: list[str] = Field(default_factory=list)
    dod_score: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


def dump_model(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def build_planning_brief(
    requirement: str,
    sources: list[dict[str, Any]],
    retrieval_status: str,
    confidence: float,
    planning_instruction: str,
) -> dict[str, Any]:
    usable_evidence = [
        {
            "evidence_id": f"E{index}",
            "source": source.get("source", "unknown source"),
            "chunk_index": source.get("chunk_index", "?"),
            "score": source.get("score", 0.0),
            "excerpt": source.get("excerpt", ""),
        }
        for index, source in enumerate(sources, start=1)
    ]
    return dump_model(
        PlanningBriefOutput.model_validate(
            {
                "requirement": requirement,
                "retrieval_status": retrieval_status,
                "confidence": confidence,
                "source_count": len(usable_evidence),
                "usable_evidence": usable_evidence,
                "planning_instruction": planning_instruction,
            }
        )
    )
