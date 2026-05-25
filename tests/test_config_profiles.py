import os
from pathlib import Path

import pytest

from ai_scrum_master.core.config import ConfigError, get_runtime_profiles


def test_runtime_profiles_load_from_default_files() -> None:
    profiles = get_runtime_profiles()
    assert {"researcher", "planner", "evaluator"}.issubset(set(profiles.agents.keys()))
    assert {"research_task", "planning_task", "evaluation_task"}.issubset(set(profiles.tasks.keys()))
    assert profiles.tasks["planning_task"].agent == "planner"


def test_runtime_profiles_fail_for_unknown_agent_mapping(tmp_path: Path) -> None:
    agents_file = tmp_path / "agents.yaml"
    tasks_file = tmp_path / "tasks.yaml"

    agents_file.write_text(
        """
agents:
  planner:
    role: Planner
    goal: Plan
    backstory: Story
""".strip(),
        encoding="utf-8",
    )
    tasks_file.write_text(
        """
tasks:
  planning_task:
    name_task: planning_task
    description: Desc
    expected_output: Out
    agent: missing_agent
""".strip(),
        encoding="utf-8",
    )

    old_agent = os.environ.get("AGENT_CONFIG_PATH")
    old_task = os.environ.get("TASK_CONFIG_PATH")
    os.environ["AGENT_CONFIG_PATH"] = str(agents_file)
    os.environ["TASK_CONFIG_PATH"] = str(tasks_file)

    try:
        with pytest.raises(ConfigError, match="unknown agent"):
            get_runtime_profiles()
    finally:
        if old_agent is None:
            os.environ.pop("AGENT_CONFIG_PATH", None)
        else:
            os.environ["AGENT_CONFIG_PATH"] = old_agent
        if old_task is None:
            os.environ.pop("TASK_CONFIG_PATH", None)
        else:
            os.environ["TASK_CONFIG_PATH"] = old_task


def test_runtime_profiles_fail_for_missing_required_task_field(tmp_path: Path) -> None:
    agents_file = tmp_path / "agents.yaml"
    tasks_file = tmp_path / "tasks.yaml"

    agents_file.write_text(
        """
agents:
  planner:
    role: Planner
    goal: Plan
    backstory: Story
""".strip(),
        encoding="utf-8",
    )
    tasks_file.write_text(
        """
tasks:
  planning_task:
    name_task: planning_task
    description: Desc
    agent: planner
""".strip(),
        encoding="utf-8",
    )

    old_agent = os.environ.get("AGENT_CONFIG_PATH")
    old_task = os.environ.get("TASK_CONFIG_PATH")
    os.environ["AGENT_CONFIG_PATH"] = str(agents_file)
    os.environ["TASK_CONFIG_PATH"] = str(tasks_file)

    try:
        with pytest.raises(ConfigError, match="expected_output"):
            get_runtime_profiles()
    finally:
        if old_agent is None:
            os.environ.pop("AGENT_CONFIG_PATH", None)
        else:
            os.environ["AGENT_CONFIG_PATH"] = old_agent
        if old_task is None:
            os.environ.pop("TASK_CONFIG_PATH", None)
        else:
            os.environ["TASK_CONFIG_PATH"] = old_task
