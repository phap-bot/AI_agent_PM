from ai_scrum_master.core.prompts import render_prompt


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
