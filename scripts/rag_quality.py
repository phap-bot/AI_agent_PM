#!/usr/bin/env python3
"""
RAG Quality Check - Đo độ tương đồng giữa query và retrieved chunks.
Dùng embedding từ nomic-embed-text qua Ollama.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.utils import embedding_functions
import numpy as np
from scripts.retrieve import get_relevant_context


class RAGQualityChecker:
    """Tính điểm tương đồng cosine giữa query và từng chunk."""

    def __init__(self):
        self.embed_fn = embedding_functions.OllamaEmbeddingFunction(
            model_name="nomic-embed-text"
        )

    def _get_embedding(self, text: str) -> list:
        """Lấy vector embedding cho một văn bản."""
        result = self.embed_fn([text])
        return result[0]

    def cosine_similarity(self, vec_a, vec_b):
        """Tính cosine similarity giữa hai vector."""
        vec_a = np.array(vec_a)
        vec_b = np.array(vec_b)
        dot = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    def evaluate_query_chunks(self, query: str, chunks: list) -> dict:
        """
        Đánh giá quality: tính similarity trung bình, max, min.
        Trả về dict với các metrics.
        """
        if not chunks:
            return {
                "avg_similarity": 0.0,
                "max_similarity": 0.0,
                "min_similarity": 0.0,
                "confidence": 0.0,
                "warnings": ["No chunks retrieved"]
            }

        query_emb = self._get_embedding(query)
        similarities = []
        for chunk in chunks:
            chunk_emb = self._get_embedding(chunk[:1000])  # giới hạn độ dài
            sim = self.cosine_similarity(query_emb, chunk_emb)
            similarities.append(sim)

        avg_sim = np.mean(similarities)
        max_sim = np.max(similarities)
        min_sim = np.min(similarities)
        # confidence = avg_sim * 100 (chuyển thành %)
        confidence = round(avg_sim * 100, 2)

        return {
            "avg_similarity": round(avg_sim, 4),
            "max_similarity": round(max_sim, 4),
            "min_similarity": round(min_sim, 4),
            "confidence": confidence,
            "warnings": [] if confidence > 30 else ["Low relevance; consider tuning retrieval"]
        }

    def quality_check_for_requirement(self, requirement: str, k: int = 3) -> dict:
        """Kết hợp retrieve và đánh giá quality."""
        chunks = get_relevant_context(requirement, k=k)
        metrics = self.evaluate_query_chunks(requirement, chunks)
        metrics["chunks"] = chunks
        metrics["num_chunks"] = len(chunks)
        return metrics


# Test nhanh
if __name__ == "__main__":
    checker = RAGQualityChecker()
    test_queries = [
        "What is a User Story?",
        "Google OAuth login",
        "Sprint planning rules"
    ]
    for q in test_queries:
        result = checker.quality_check_for_requirement(q, k=3)
        print(f"\nQuery: {q}")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Avg similarity: {result['avg_similarity']}")
        print(f"  Warnings: {result['warnings']}")