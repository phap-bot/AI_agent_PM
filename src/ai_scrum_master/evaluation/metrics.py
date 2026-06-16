import math
import re
import json
from typing import Any

from ai_scrum_master.core.utils.logging import get_logger

logger = get_logger(__name__)

# ==============================================================================
# RETRIEVAL METRICS (Requires Ground Truth)
# ==============================================================================

def calculate_precision_k(retrieved_ids: list[str], expected_ids: set[str], k: int) -> float:
    """Calculate Precision@k: fraction of retrieved items at k that are relevant."""
    if not retrieved_ids or k <= 0:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_count = sum(1 for item in top_k if item in expected_ids)
    return round(relevant_count / len(top_k), 3)


def calculate_recall_k(retrieved_ids: list[str], expected_ids: set[str], k: int) -> float:
    """Calculate Recall@k: fraction of expected items successfully retrieved at k."""
    if not expected_ids or not retrieved_ids or k <= 0:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_count = sum(1 for item in top_k if item in expected_ids)
    return round(relevant_count / len(expected_ids), 3)


def calculate_mrr(retrieved_ids: list[str], expected_ids: set[str]) -> float:
    """Calculate Mean Reciprocal Rank (MRR) for the first relevant item."""
    if not retrieved_ids or not expected_ids:
        return 0.0
    for i, item in enumerate(retrieved_ids):
        if item in expected_ids:
            return round(1.0 / (i + 1), 3)
    return 0.0


def calculate_ndcg_k(retrieved_ids: list[str], expected_ids: set[str], k: int) -> float:
    """Calculate Normalized Discounted Cumulative Gain at k (binary relevance)."""
    if not retrieved_ids or not expected_ids or k <= 0:
        return 0.0
    
    dcg = 0.0
    for i, item in enumerate(retrieved_ids[:k]):
        if item in expected_ids:
            dcg += 1.0 / math.log2(i + 2) # i=0 -> log2(2) = 1
            
    idcg = 0.0
    ideal_k = min(len(expected_ids), k)
    for i in range(ideal_k):
        idcg += 1.0 / math.log2(i + 2)
        
    if idcg == 0.0:
        return 0.0
    return round(dcg / idcg, 3)


# ==============================================================================
# RAG METRICS (LLM-as-a-judge)
# ==============================================================================

def evaluate_faithfulness(question: str, answer: str, contexts: list[str], llm=None) -> dict[str, Any]:
    """
    Evaluates whether the generated answer is faithful to the provided contexts.
    Returns a score from 0.0 to 1.0 and a reasoning string.
    """
    if not contexts or not answer or answer.strip() == "":
        return {"score": 0.0, "reasoning": "Missing answer or context."}

    if not llm:
        from ai_scrum_master.core.llm.setup import build_llm
        llm = build_llm(temperature=0.0)

    combined_context = "\n\n".join(f"[Context {i+1}]: {c}" for i, c in enumerate(contexts))
    
    prompt = f"""You are an objective evaluator. Given a question, an answer, and a set of contexts, your task is to evaluate if the answer is FAITHFUL to the contexts.
Faithful means all claims made in the answer can be directly inferred from the contexts.
Do not use outside knowledge.

Question: {question}

Contexts:
{combined_context}

Answer: {answer}

Output your evaluation in strict JSON format with exactly these two keys:
- "score": A float between 0.0 and 1.0 (1.0 = fully faithful, 0.0 = completely hallucinated).
- "reasoning": A brief explanation of why this score was given.
"""
    try:
        response = llm.call([{"role": "user", "content": prompt}])
        result = _parse_json_llm_response(response)
        score = float(result.get("score", 0.0))
        reasoning = str(result.get("reasoning", "Parse error"))
        return {"score": round(max(0.0, min(1.0, score)), 3), "reasoning": reasoning}
    except Exception as e:
        logger.warning(f"Faithfulness evaluation failed: {e}")
        return {"score": 0.0, "reasoning": f"Evaluation error: {e}"}


def evaluate_answer_relevancy(question: str, answer: str, llm=None) -> dict[str, Any]:
    """
    Evaluates whether the answer directly addresses the question.
    Returns a score from 0.0 to 1.0 and a reasoning string.
    """
    if not question or not answer or answer.strip() == "":
        return {"score": 0.0, "reasoning": "Missing question or answer."}

    if not llm:
        from ai_scrum_master.core.llm.setup import build_llm
        llm = build_llm(temperature=0.0)

    prompt = f"""You are an objective evaluator. Given a question and an answer, evaluate how RELEVANT the answer is to the question.
An answer is relevant if it directly addresses the user's core intent without excessive fluff or dodging the question.

Question: {question}

Answer: {answer}

Output your evaluation in strict JSON format with exactly these two keys:
- "score": A float between 0.0 and 1.0 (1.0 = perfectly relevant, 0.0 = completely irrelevant).
- "reasoning": A brief explanation of why this score was given.
"""
    try:
        response = llm.call([{"role": "user", "content": prompt}])
        result = _parse_json_llm_response(response)
        score = float(result.get("score", 0.0))
        reasoning = str(result.get("reasoning", "Parse error"))
        return {"score": round(max(0.0, min(1.0, score)), 3), "reasoning": reasoning}
    except Exception as e:
        logger.warning(f"Answer relevancy evaluation failed: {e}")
        return {"score": 0.0, "reasoning": f"Evaluation error: {e}"}


def _parse_json_llm_response(text: str) -> dict:
    text = str(text)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
        
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
            
    return {"score": 0.0, "reasoning": "Could not parse JSON response from LLM."}
