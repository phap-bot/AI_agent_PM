from __future__ import annotations

from importlib import resources


PROMPT_PACKAGE = "ai_scrum_master.prompts"


class PromptTemplateError(ValueError):
    pass


def render_prompt(template_name: str, **values: object) -> str:
    try:
        template = resources.files(PROMPT_PACKAGE).joinpath(template_name).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise PromptTemplateError(f"Prompt template not found: {template_name}") from exc

    try:
        values.setdefault("planning_brief_json", "{}")
        values.setdefault("task_description", "")
        values.setdefault("expected_output", "")
        values.setdefault("repair_blockers", "[]")
        return template.format(**values).strip()
    except KeyError as exc:
        missing_key = exc.args[0]
        raise PromptTemplateError(f"Prompt template '{template_name}' is missing value for '{missing_key}'") from exc
