from __future__ import annotations

from typing import Any

from ai_scrum_master.core.config import get_settings


def build_llm(**overrides: Any) -> Any:
    from crewai import LLM

    settings = get_settings()
    options = {
        "num_ctx": settings.ollama_num_ctx,
        **overrides.pop("options", {}),
    }

    return LLM(
        model=f"ollama/{settings.reasoning_model}",
        base_url=settings.ollama_base_url,
        temperature=settings.ollama_temperature,
        timeout=settings.ollama_timeout,
        extra_body={"options": options},
        **overrides,
    )
