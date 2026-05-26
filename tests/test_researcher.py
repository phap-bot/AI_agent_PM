#!/usr/bin/env python3
"""
Unit tests for Researcher Agent.
"""

import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import đúng module
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from scripts.researcher_agent import ResearcherAgent


class TestResearcherAgent:
    """Test suite for ResearcherAgent."""

    @pytest.fixture
    def agent(self):
        """Khởi tạo agent ở chế độ raw (không dùng LLM) để test nhanh."""
        return ResearcherAgent(use_llm_summary=False)

    def test_agent_initialization(self, agent):
        """Test T3.3.1: Agent khởi tạo đúng."""
        assert agent is not None
        assert hasattr(agent, 'research')
        assert hasattr(agent, 'run')

    def test_research_returns_dict(self, agent):
        """Test T3.3.2: Hàm research trả về dict đúng cấu trúc."""
        result = agent.research("What is Scrum?", k=2)
        assert isinstance(result, dict)
        assert 'documents' in result
        assert 'metadatas' in result
        assert 'warnings' in result

    def test_research_returns_list(self, agent):
        """Test T3.3.3: Research trả về danh sách documents."""
        result = agent.research("Scrum", k=3)
        assert isinstance(result['documents'], list)

    def test_run_returns_string(self, agent):
        """Test T3.3.4: Hàm run trả về string."""
        result = agent.run("What is a User Story?", k=2)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_request_handling(self, agent):
        """Test T3.3.5: Xử lý request rỗng."""
        result = agent.run("", k=2)
        assert isinstance(result, str)

    def test_k_parameter_works(self, agent):
        """Test T3.3.6: Tham số k hoạt động đúng."""
        result_k1 = agent.run("Scrum", k=1)
        result_k3 = agent.run("Scrum", k=3)
        assert isinstance(result_k1, str)
        assert isinstance(result_k3, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])