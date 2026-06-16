import json
import logging
from typing import Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class MetricResult(BaseModel):
    score: float
    reasoning: str

def evaluate_story_point_error(predicted: Any, actual: Any) -> float:
    """Calculates absolute error for story points. If unparseable, returns high error penalty."""
    try:
        p_val = float(predicted) if predicted else 0.0
        a_val = float(actual) if actual else 0.0
        return abs(p_val - a_val)
    except (ValueError, TypeError):
        return 999.0  # Penalty for invalid format

def evaluate_classification(predicted: str, actual: str) -> float:
    """Exact match score for categorical fields like issue type and priority."""
    if not predicted or not actual:
        return 0.0
    return 1.0 if str(predicted).strip().lower() == str(actual).strip().lower() else 0.0

def _run_llm_judge(llm: Any, prompt: str) -> MetricResult:
    try:
        messages = [{"role": "user", "content": prompt}]
        response = llm.call(messages)
        text = response if isinstance(response, str) else str(response)
        
        # Clean markdown formatting if present
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        
        return MetricResult(
            score=float(result.get("score", 0.0)),
            reasoning=str(result.get("reasoning", "Failed to parse reasoning"))
        )
    except Exception as e:
        logger.error(f"LLM Judge evaluation failed: {e}")
        return MetricResult(score=0.0, reasoning=f"Evaluation failed: {e}")

def evaluate_coverage(llm: Any, original_description: str, generated_tasks: str) -> MetricResult:
    prompt = f"""You are an expert Agile Coach evaluating an AI Planner Agent.
Evaluate the 'Coverage' of the generated Work Breakdown Structure (WBS).
Does the generated WBS cover all the functional requirements and acceptance criteria mentioned in the original issue description?

Original Issue Description:
{original_description}

Generated WBS / Task List:
{generated_tasks}

Output strictly in JSON format with two keys:
- "score": A float between 0.0 and 1.0 (1.0 = full coverage, 0.5 = partial coverage, 0.0 = misses most points).
- "reasoning": A brief explanation of why this score was given, highlighting any missing elements.
"""
    return _run_llm_judge(llm, prompt)

def evaluate_completeness(llm: Any, original_description: str, generated_tasks: str) -> MetricResult:
    prompt = f"""You are an expert QA Engineer evaluating an AI Planner Agent.
Evaluate the 'Completeness' of the generated Work Breakdown Structure (WBS).
Did the agent anticipate and include necessary edge cases, testing tasks, error handling, or non-functional requirements (security, performance) that weren't explicitly stated but are required for completeness?

Original Issue Description:
{original_description}

Generated WBS / Task List:
{generated_tasks}

Output strictly in JSON format with two keys:
- "score": A float between 0.0 and 1.0 (1.0 = highly complete with edge cases covered, 0.0 = naive happy-path only).
- "reasoning": A brief explanation of the score.
"""
    return _run_llm_judge(llm, prompt)

def evaluate_breakdown_quality(llm: Any, generated_tasks: str) -> MetricResult:
    prompt = f"""You are an expert Technical Project Manager evaluating an AI Planner Agent.
Evaluate the 'Breakdown Quality' (Granularity & Clarity) of the generated Work Breakdown Structure (WBS).
Are the tasks appropriately sized (not too massive, not ridiculously micro)? Are the titles and descriptions clear, actionable, and following INVEST principles?

Generated WBS / Task List:
{generated_tasks}

Output strictly in JSON format with two keys:
- "score": A float between 0.0 and 1.0 (1.0 = perfect granularity and clarity, 0.0 = poor structure/too vague).
- "reasoning": A brief explanation of the score.
"""
    return _run_llm_judge(llm, prompt)
