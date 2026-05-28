from pathlib import Path


def test_obsolete_quality_shims_are_removed() -> None:
    core_dir = Path("src/ai_scrum_master/core")

    assert not (core_dir / "retrieval_quality.py").exists()
    assert not (core_dir / "post_generation_validator.py").exists()


def test_obsolete_core_retrieval_shims_are_removed() -> None:
    core_dir = Path("src/ai_scrum_master/core")

    assert not (core_dir / "RAG.py").exists()
    assert not (core_dir / "vector_store.py").exists()


def test_obsolete_agent_action_tool_shims_are_removed() -> None:
    tools_dir = Path("src/ai_scrum_master/agents/tools")

    assert not (tools_dir / "jira_tool.py").exists()
    assert not (tools_dir / "slack_tool.py").exists()


def test_research_quality_lives_in_quality_gate_not_agent_quality() -> None:
    agent_quality_path = Path("src/ai_scrum_master/core/agent_quality.py")

    assert not agent_quality_path.exists()


def test_planner_quality_lives_in_story_validator_not_agent_quality() -> None:
    agent_quality_path = Path("src/ai_scrum_master/core/agent_quality.py")

    assert not agent_quality_path.exists()


def test_runtime_code_imports_retrieval_package_not_core_retrieval_shims() -> None:
    source_files = list(Path("src/ai_scrum_master").rglob("*.py"))
    runtime_imports = "\n".join(
        path.read_text(encoding="utf-8")
        for path in source_files
        if path.name not in {"RAG.py", "vector_store.py"}
    )

    assert "ai_scrum_master.core.RAG" not in runtime_imports
    assert "ai_scrum_master.core.vector_store" not in runtime_imports


def test_pipeline_service_and_crewai_builder_are_separate() -> None:
    pipeline_path = Path("src/ai_scrum_master/core/pipeline.py")
    agents_crew_path = Path("src/ai_scrum_master/agents/crew.py")

    assert pipeline_path.exists()
    assert agents_crew_path.exists()
    agents_crew_source = agents_crew_path.read_text(encoding="utf-8")
    assert "build_scrum_master_crew" in agents_crew_source
    assert "ai_scrum_master.actions" not in agents_crew_source
    assert "ai_scrum_master.core.pipeline" not in agents_crew_source


def test_generate_router_delegates_to_pipeline_service() -> None:
    generate_router_path = Path("src/ai_scrum_master/api/routers/generate.py")
    source = generate_router_path.read_text(encoding="utf-8")

    assert "generate_story_pipeline" in source
    assert ".run(" not in source


def test_pipeline_service_builds_crewai_crew_for_current_request() -> None:
    pipeline_path = Path("src/ai_scrum_master/core/pipeline.py")
    source = pipeline_path.read_text(encoding="utf-8")

    assert "build_scrum_master_crew" in source
    assert "crewai_crew" in source


def test_core_pipeline_does_not_duplicate_crewai_task_assembly() -> None:
    pipeline_path = Path("src/ai_scrum_master/core/pipeline.py")
    source = pipeline_path.read_text(encoding="utf-8")

    assert "ScrumMasterTasks" not in source
    assert "build_crewai_blueprint" not in source
