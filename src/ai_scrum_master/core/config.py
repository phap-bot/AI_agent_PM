from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values, load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
PROFILE_ENV_VAR = "AI_SCRUM_PROFILE"


def _profile_name() -> str:
    return os.getenv(PROFILE_ENV_VAR, "").strip()


def _profile_env_path(profile: str) -> Path:
    safe_profile = profile.replace("/", "").replace("\\", "").strip(". ")
    return BASE_DIR / f".env.{safe_profile}"


def _load_profile_env(profile: str, protected_keys: set[str]) -> None:
    if not profile:
        return
    profile_path = _profile_env_path(profile)
    if not profile_path.exists():
        return

    for key, value in dotenv_values(profile_path).items():
        if value is not None and key not in protected_keys:
            os.environ[key] = value


_PROTECTED_ENV_KEYS = set(os.environ)
load_dotenv(BASE_DIR / ".env", override=False)
_load_profile_env(_profile_name(), _PROTECTED_ENV_KEYS)


class ConfigError(ValueError):
    pass


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _path_env(name: str, default: Path) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        return str(default.resolve())
    path = Path(value.strip())
    if not path.is_absolute():
        path = BASE_DIR / path
    return str(path.resolve())


@dataclass(frozen=True)
class Settings:
    config_profile: str = field(default_factory=lambda: _profile_name() or "default")
    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "AI Scrum Master Agent"))
    app_version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "0.1.0"))
    ollama_base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    reasoning_model: str = field(default_factory=lambda: os.getenv("OLLAMA_REASONING_MODEL", "qwen2.5:3b-instruct"))
    embedding_model: str = field(default_factory=lambda: os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"))
    ollama_timeout: int = field(default_factory=lambda: int(os.getenv("OLLAMA_TIMEOUT", "240")))
    ollama_num_ctx: int = field(default_factory=lambda: int(os.getenv("OLLAMA_NUM_CTX", "2048")))
    ollama_num_gpu: int = field(default_factory=lambda: int(os.getenv("OLLAMA_NUM_GPU", "-1")))
    ollama_temperature: float = field(default_factory=lambda: float(os.getenv("OLLAMA_TEMPERATURE", "0.2")))
    chroma_persist_dir: str = field(default_factory=lambda: _path_env("CHROMA_PERSIST_DIR", BASE_DIR / "data" / "chromadb"))
    context_collection: str = field(default_factory=lambda: os.getenv("CHROMA_COLLECTION", "ai_scrum_master_context"))
    rag_backend: str = field(default_factory=lambda: os.getenv("RAG_BACKEND", "langchain"))
    rag_fallback_to_direct_chroma: bool = field(default_factory=lambda: _bool_env("RAG_FALLBACK_TO_DIRECT_CHROMA", True))
    rag_chunk_size: int = field(default_factory=lambda: int(os.getenv("RAG_CHUNK_SIZE", "1200")))
    rag_chunk_overlap: int = field(default_factory=lambda: int(os.getenv("RAG_CHUNK_OVERLAP", "200")))
    pdf_extractor: str = field(default_factory=lambda: os.getenv("PDF_EXTRACTOR", "auto"))
    pdf_remove_headers_footers: bool = field(default_factory=lambda: _bool_env("PDF_REMOVE_HEADERS_FOOTERS", True))
    pdf_semantic_chunking: bool = field(default_factory=lambda: _bool_env("PDF_SEMANTIC_CHUNKING", True))
    pdf_fallback_on_error: bool = field(default_factory=lambda: _bool_env("PDF_FALLBACK_ON_ERROR", True))
    rag_hybrid_search: bool = field(default_factory=lambda: _bool_env("RAG_HYBRID_SEARCH", True))
    rag_vector_fetch_k: int = field(default_factory=lambda: int(os.getenv("RAG_VECTOR_FETCH_K", "20")))
    planner_prompt_version: str = field(default_factory=lambda: os.getenv("PLANNER_PROMPT_VERSION", "current"))
    planner_max_repair_attempts: int = field(default_factory=lambda: int(os.getenv("PLANNER_MAX_REPAIR_ATTEMPTS", "3")))
    retrieval_min_score: float = field(default_factory=lambda: float(os.getenv("RETRIEVAL_MIN_SCORE", "0.6")))
    retrieval_excerpt_chars: int = field(default_factory=lambda: int(os.getenv("RETRIEVAL_EXCERPT_CHARS", "300")))
    retrieval_context_top_k: int = field(default_factory=lambda: int(os.getenv("RETRIEVAL_CONTEXT_TOP_K", "3")))
    jira_base_url: str = field(default_factory=lambda: os.getenv("JIRA_BASE_URL", ""))
    jira_project_key: str = field(default_factory=lambda: os.getenv("JIRA_PROJECT_KEY", ""))
    jira_email: str = field(default_factory=lambda: os.getenv("JIRA_EMAIL", ""))
    jira_api_token: str = field(default_factory=lambda: os.getenv("JIRA_API_TOKEN", ""))
    jira_issue_type: str = field(default_factory=lambda: os.getenv("JIRA_ISSUE_TYPE", "Task"))
    jira_subtask_issue_type: str = field(default_factory=lambda: os.getenv("JIRA_SUBTASK_ISSUE_TYPE", "Sub-task"))
    slack_webhook_url: str = field(default_factory=lambda: os.getenv("SLACK_WEBHOOK_URL", ""))
    slack_mention_user_id: str = field(default_factory=lambda: os.getenv("SLACK_MENTION_USER_ID", ""))
    agent_config_path: str = field(
        default_factory=lambda: os.getenv(
            "AGENT_CONFIG_PATH",
            str(BASE_DIR / "config" / "agents" / "default.yaml"),
        )
    )
    task_config_path: str = field(
        default_factory=lambda: os.getenv(
            "TASK_CONFIG_PATH",
            str(BASE_DIR / "config" / "tasks" / "default.yaml"),
        )
    )


@dataclass(frozen=True)
class AgentProfileConfig:
    name: str
    role: str
    goal: str
    backstory: str


@dataclass(frozen=True)
class TaskProfileConfig:
    name_task: str
    description: str
    expected_output: str
    agent: str


@dataclass(frozen=True)
class RuntimeProfilesConfig:
    agents: dict[str, AgentProfileConfig]
    tasks: dict[str, TaskProfileConfig]


def get_settings() -> Settings:
    return Settings()


def _read_yaml_config(path: str) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        raise ConfigError(f"Config file not found: {file_path}")

    try:
        with file_path.open("r", encoding="utf-8") as file:
            payload = yaml.safe_load(file) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML format in {file_path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ConfigError(f"Config root must be an object in {file_path}")
    return payload


def _required_str(payload: dict[str, Any], key: str, source: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Missing required field '{key}' in {source}")
    return value.strip()


def get_agent_profiles() -> dict[str, AgentProfileConfig]:
    settings = get_settings()
    payload = _read_yaml_config(settings.agent_config_path)
    agents_payload = payload.get("agents", {})
    if not isinstance(agents_payload, dict) or not agents_payload:
        raise ConfigError("Agent config must define a non-empty 'agents' object")

    profiles: dict[str, AgentProfileConfig] = {}
    for name, value in agents_payload.items():
        if not isinstance(value, dict):
            raise ConfigError(f"Agent '{name}' config must be an object")
        profiles[name] = AgentProfileConfig(
            name=name,
            role=_required_str(value, "role", f"agents.{name}"),
            goal=_required_str(value, "goal", f"agents.{name}"),
            backstory=_required_str(value, "backstory", f"agents.{name}"),
        )
    return profiles


def get_task_profiles() -> dict[str, TaskProfileConfig]:
    settings = get_settings()
    payload = _read_yaml_config(settings.task_config_path)
    tasks_payload = payload.get("tasks", {})
    if not isinstance(tasks_payload, dict) or not tasks_payload:
        raise ConfigError("Task config must define a non-empty 'tasks' object")

    profiles: dict[str, TaskProfileConfig] = {}
    for key, value in tasks_payload.items():
        if not isinstance(value, dict):
            raise ConfigError(f"Task '{key}' config must be an object")
        profiles[key] = TaskProfileConfig(
            name_task=_required_str(value, "name_task", f"tasks.{key}"),
            description=_required_str(value, "description", f"tasks.{key}"),
            expected_output=_required_str(value, "expected_output", f"tasks.{key}"),
            agent=_required_str(value, "agent", f"tasks.{key}"),
        )
    return profiles


def get_runtime_profiles() -> RuntimeProfilesConfig:
    agents = get_agent_profiles()
    tasks = get_task_profiles()

    for task_key, task in tasks.items():
        if task.agent not in agents:
            raise ConfigError(
                f"Task '{task_key}' references unknown agent '{task.agent}'"
            )

    return RuntimeProfilesConfig(agents=agents, tasks=tasks)
