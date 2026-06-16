from __future__ import annotations

from ai_scrum_master.core.utils.logging import get_logger

logger = get_logger(__name__)


def normalize_llm_json_output(raw_output: object) -> str:
    text = str(raw_output).strip()
    
    think_start = text.find("<think>")
    think_end = text.find("</think>")
    if think_start != -1 and think_end != -1 and think_end > think_start:
        think_content = text[think_start + 7:think_end].strip()
        logger.info("LLM Internal Thinking Trace:\n%s", think_content)
        text = text[:think_start] + text[think_end + 8:]
        text = text.strip()

    text = _strip_outer_fence(text)
    
    # For models like Qwen that do reasoning before the JSON block without <think> tags
    start_idx = text.find("{")
    if start_idx > 0:
        pre_text = text[:start_idx].strip()
        if pre_text:
            logger.info("LLM Pre-JSON Reasoning Trace:\n%s", pre_text)
            
    return _extract_json_object(text)


def _strip_outer_fence(text: str) -> str:
    stripped = text.strip()
    for fence in ("```", "'''"):
        if stripped.startswith(fence) and stripped.endswith(fence):
            inner = stripped[len(fence) : -len(fence)].strip()
            lowered = inner.lower()
            if lowered.startswith("json"):
                inner = inner[4:].strip()
            return inner
    return stripped


def _extract_json_object(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    start = stripped.find("{")
    if start == -1:
        raise ValueError("LLM output did not contain a JSON object.")

    in_string = False
    escaped = False
    depth = 0
    for index in range(start, len(stripped)):
        char = stripped[index]
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_string:
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return stripped[start : index + 1].strip()

    raise ValueError("LLM output contained an incomplete JSON object.")
