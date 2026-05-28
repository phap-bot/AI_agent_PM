from ai_scrum_master.core.prompts import render_prompt
from pathlib import Path


def test_render_prompt_loads_packaged_template() -> None:
    prompt = render_prompt(
        "planner.md",
        role="Planner Agent",
        goal="Convert requirements",
        backstory="Supports Scrum planning",
        requirement="Add Google login",
        planning_status="READY",
        context_block="Auth uses JWT",
    )

    assert "You are Planner Agent." in prompt
    assert "Add Google login" in prompt
    assert "Return only valid JSON" in prompt
    assert "Do not use fixed template business content" in prompt
    assert "Generate content from CURRENT_REQUIREMENT and SELECTED_RETRIEVED_CONTEXT" in prompt
    assert "SELECTED_RETRIEVED_CONTEXT" in prompt
    assert "RESEARCH_PLANNING_BRIEF" in prompt
    assert "context_sources must contain only sources actually used" in prompt


def test_obsolete_prompt_versions_are_removed() -> None:
    prompt_dir = Path("src/ai_scrum_master/prompts")

    assert not (prompt_dir / "planner_v2.md").exists()
    assert not (prompt_dir / "planner_repair_v2.md").exists()
