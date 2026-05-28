from __future__ import annotations

from fastapi import APIRouter, Depends

from ai_scrum_master.api.schemas import GenerateStoriesRequest, GenerateStoriesResponse
from ai_scrum_master.core.pipeline import ScrumMasterCrew, generate_story_pipeline

router = APIRouter()


def get_crew() -> ScrumMasterCrew:
    return ScrumMasterCrew()


@router.post("/generate", response_model=GenerateStoriesResponse)
def generate_stories(
    payload: GenerateStoriesRequest,
    crew: ScrumMasterCrew = Depends(get_crew),
) -> GenerateStoriesResponse:
    result = generate_story_pipeline(
        requirement=payload.requirement,
        n_results=payload.n_results,
        allow_fallback_without_context=payload.allow_fallback_without_context,
        crew=crew,
    )
    return GenerateStoriesResponse(**result)
