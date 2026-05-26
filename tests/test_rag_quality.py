import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from scripts.rag_quality import RAGQualityChecker


class TestRAGQuality:
    @pytest.fixture
    def checker(self):
        return RAGQualityChecker()

    def test_cosine_similarity(self, checker):
        vec1 = [1.0, 0.0]
        vec2 = [1.0, 0.0]
        assert checker.cosine_similarity(vec1, vec2) == 1.0

        vec3 = [1.0, 0.0]
        vec4 = [0.0, 1.0]
        assert checker.cosine_similarity(vec3, vec4) == 0.0

    def test_evaluate_query_chunks_empty(self, checker):
        result = checker.evaluate_query_chunks("test", [])
        assert result["confidence"] == 0.0
        assert "No chunks retrieved" in result["warnings"][0]

    def test_evaluate_query_chunks_with_data(self, checker):
        # Lấy context thật từ ChromaDB
        from scripts.retrieve import get_relevant_context
        chunks = get_relevant_context("Scrum", k=2)
        if chunks:
            result = checker.evaluate_query_chunks("Scrum", chunks)
            assert "confidence" in result
            assert isinstance(result["confidence"], float)