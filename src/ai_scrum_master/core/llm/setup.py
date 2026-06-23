from __future__ import annotations

from typing import Any

from ai_scrum_master.core.config.settings import get_settings


def build_llm(**overrides: Any) -> Any:
    from crewai import LLM

    settings = get_settings()
    options = {
        "num_ctx": settings.ollama_num_ctx,
        "num_gpu": settings.ollama_num_gpu,
        "keep_alive": "0",  # Unload immediately to save VRAM
        **overrides.pop("options", {}),
    }

    return LLM(
        model=overrides.pop("model", f"ollama/{settings.reasoning_model}"),
        base_url=overrides.pop("base_url", settings.ollama_base_url),
        temperature=overrides.pop("temperature", settings.ollama_temperature),
        timeout=overrides.pop("timeout", settings.ollama_timeout),
        extra_body={"options": options},
        **overrides,
    )
