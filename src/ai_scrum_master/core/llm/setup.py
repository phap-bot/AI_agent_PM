from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from ai_scrum_master.core.config.settings import get_settings


class ChatOllamaCallAdapter:
    """Expose a small .call(messages) contract over LangChain ChatOllama."""

    def __init__(self, llm: Any) -> None:
        self._llm = llm

    def call(self, messages: list[dict[str, str]], *args: Any, **kwargs: Any) -> str:
        response = self._llm.invoke(_to_langchain_messages(messages), *args, **kwargs)
        return str(getattr(response, "content", response))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._llm, name)


class LoggedLLM:
    def __init__(self, llm: Any) -> None:
        self._llm = llm

    def call(self, messages: list[dict[str, str]], *args: Any, **kwargs: Any) -> str:
        started_at = time.time()
        response = self._llm.call(messages, *args, **kwargs)
        elapsed = time.time() - started_at

        if os.environ.get("ENABLE_LLM_LOGGING") == "1":
            try:
                log_dir = Path(os.environ.get("LLM_LOG_DIR", "data/llm_logs"))
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

    def __getattr__(self, name: str) -> Any:
        return getattr(self._llm, name)


def build_llm(**overrides: Any) -> Any:
    from langchain_ollama import ChatOllama

    settings = get_settings()
    model = _normalize_ollama_model_name(overrides.pop("model", settings.reasoning_model))
    timeout = overrides.pop("timeout", settings.ollama_timeout)
    client_kwargs = dict(overrides.pop("client_kwargs", {}) or {})
    client_kwargs.setdefault("timeout", timeout)

    options = {
        "num_ctx": settings.ollama_num_ctx,
        "num_gpu": settings.ollama_num_gpu,
        **overrides.pop("options", {}),
    }

    base_llm = ChatOllama(
        model=model,
        base_url=overrides.pop("base_url", settings.ollama_base_url),
        temperature=overrides.pop("temperature", settings.ollama_temperature),
        keep_alive=overrides.pop("keep_alive", "0"),
        client_kwargs=client_kwargs,
        **options,
        **overrides,
    )
    return LoggedLLM(ChatOllamaCallAdapter(base_llm))


def _normalize_ollama_model_name(model: str) -> str:
    prefix = "ollama/"
    return model[len(prefix):] if model.startswith(prefix) else model


def _to_langchain_messages(messages: list[dict[str, str]]) -> list[Any]:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    converted = []
    for message in messages:
        role = str(message.get("role", "user")).lower()
        content = str(message.get("content", ""))
        if role == "system":
            converted.append(SystemMessage(content=content))
        elif role == "assistant":
            converted.append(AIMessage(content=content))
        else:
            converted.append(HumanMessage(content=content))
    return converted
