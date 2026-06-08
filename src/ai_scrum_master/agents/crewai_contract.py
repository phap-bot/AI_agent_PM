from __future__ import annotations

from dataclasses import dataclass, field
from textwrap import dedent
from typing import Any


@dataclass(frozen=True)
class CrewAgentSpec:
    role: str
    goal: str
    backstory: str
    tools: list[Any] = field(default_factory=list)
    verbose: bool = True
    allow_delegation: bool = False


@dataclass(frozen=True)
class CrewTaskSpec:
    description: str
    agent: Any
    expected_output: str
    context: list[Any] = field(default_factory=list)
    output_pydantic: Any = None


def build_crewai_agent(
    *,
    role: str,
    goal: str,
    backstory: str,
    tools: list[Any] | None = None,
    verbose: bool = True,
    allow_delegation: bool = False,
    llm: Any = None,
) -> Any:
    payload = {
        "role": role,
        "goal": goal,
        "backstory": dedent(backstory).strip(),
        "tools": tools or [],
        "verbose": verbose,
        "allow_delegation": allow_delegation,
    }
    if llm is not None:
        payload["llm"] = llm
    try:
        from crewai import Agent
    except Exception:
        return CrewAgentSpec(**payload)
    try:
        return Agent(**payload)
    except Exception:
        return CrewAgentSpec(**payload)


def build_crewai_task(
    *,
    description: str,
    agent: Any,
    expected_output: str,
    context: list[Any] | None = None,
    output_pydantic: Any = None,
) -> Any:
    payload = {
        "description": dedent(description).strip(),
        "agent": agent,
        "expected_output": expected_output,
    }
    if context is not None:
        payload["context"] = context
    if output_pydantic is not None:
        payload["output_pydantic"] = output_pydantic
    try:
        from crewai import Task
    except Exception:
        return CrewTaskSpec(**payload)
    try:
        return Task(**payload)
    except Exception:
        return CrewTaskSpec(**payload)
