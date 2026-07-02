from __future__ import annotations

from typing import Any

from ai_scrum_master.core.config.settings import get_settings


import os
import json
import time
from pathlib import Path

class LoggedLLM:
    def __init__(self, llm):
        self._llm = llm

    def call(self, messages, *args, **kwargs):
        started_at = time.time()
        response = self._llm.call(messages, *args, **kwargs)
        elapsed = time.time() - started_at

        if os.environ.get("ENABLE_LLM_LOGGING") == "1":
            try:
                log_dir = Path("d:/Antigravity/AI_Agent_PM_PRJ/data/llm_logs")
                log_dir.mkdir(parents=True, exist_ok=True)
                log_file = log_dir / f"llm_log_{int(started_at * 1000)}.json"
                log_data = {
                    "timestamp": started_at,
                    "elapsed_s": elapsed,
                    "messages": messages,
                    "response": response
                }
                with open(log_file, "w", encoding="utf-8") as f:
                    json.dump(log_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"[LoggedLLM] Failed to write log: {e}")

        return response

    def __getattr__(self, name):
        return getattr(self._llm, name)

def build_llm(**overrides: Any) -> Any:
    from crewai import LLM

    settings = get_settings()
    options = {
        "num_ctx": settings.ollama_num_ctx,
        "num_gpu": settings.ollama_num_gpu,
        "keep_alive": "0",  # Unload immediately to save VRAM
        **overrides.pop("options", {}),
    }

    base_llm = LLM(
        model=overrides.pop("model", f"ollama/{settings.reasoning_model}"),
        base_url=overrides.pop("base_url", settings.ollama_base_url),
        temperature=overrides.pop("temperature", settings.ollama_temperature),
        timeout=overrides.pop("timeout", settings.ollama_timeout),
        extra_body={"options": options},
        **overrides,
    )
    return LoggedLLM(base_llm)
