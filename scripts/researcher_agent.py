#!/usr/bin/env python3
"""
Researcher Agent - Dùng CrewAI để truy xuất context từ ChromaDB.
Hoàn thành các task T3.1, T3.2 trong tuần 3.
"""

import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import module scripts.retrieve
sys.path.insert(0, str(Path(__file__).parent.parent))

from crewai import Agent, Task, Crew
from scripts.retrieve import get_relevant_context


class ResearcherAgent:
    """
    Researcher Agent: Tra ChromaDB và trả về context.
    Có thể chạy ở chế độ raw (chỉ trả chunk) hoặc dùng LLM để tổng hợp.
    """

    def __init__(self, use_llm_summary: bool = False):
        """
        Args:
            use_llm_summary: Nếu True, agent sẽ dùng LLM (deepseek) để tóm tắt context.
                             Nếu False, chỉ trả về raw chunks (nhanh hơn, tiết kiệm tài nguyên).
        """
        self.use_llm_summary = use_llm_summary
        if use_llm_summary:
            self.agent = Agent(
                role="Researcher",
                goal="Truy xuất thông tin liên quan từ cơ sở kiến thức Agile/Scrum",
                backstory="""Bạn là chuyên gia nghiên cứu tài liệu. Bạn tìm kiếm trong ChromaDB
                các đoạn văn bản liên quan nhất, sau đó tổng hợp thành một bản tóm tắt ngắn gọn,
                chỉ dùng thông tin thực tế có trong tài liệu, không tự suy diễn.""",
                verbose=True,
                allow_delegation=False,
                llm="ollama/deepseek-r1:7b"
            )

    def research(self, requirement: str, k: int = 3) -> dict:
        """
        Truy xuất context từ ChromaDB.
        Trả về dict chứa documents, metadatas (tạm), distances.
        """
        chunks = get_relevant_context(requirement, k=k)
        return {
            "documents": chunks,
            "metadatas": [{"source": "unknown"}] * len(chunks),
            "distances": [],
            "warnings": [] if chunks else ["No relevant context found."]
        }

    def run(self, requirement: str, k: int = 3) -> str:
        """
        Chạy researcher: trả về context dạng text.
        """
        context_data = self.research(requirement, k)

        if not context_data["documents"]:
            return "Không tìm thấy thông tin liên quan trong cơ sở kiến thức."

        raw_text = "\n---\n".join(context_data["documents"])

        if self.use_llm_summary:
            task = Task(
                description=f"""
                Yêu cầu từ người dùng: "{requirement}"

                Các đoạn thông tin từ cơ sở kiến thức:
                {raw_text}

                Nhiệm vụ: Viết một đoạn tóm tắt ngắn gọn (dưới 300 chữ) chỉ chứa các thông tin thực tế
                từ các đoạn trên. Không thêm suy luận. Nếu thông tin không liên quan, hãy nói rõ.
                """,
                expected_output="Một đoạn tóm tắt context ngắn gọn.",
                agent=self.agent
            )
            crew = Crew(agents=[self.agent], tasks=[task], verbose=False)
            summary = crew.kickoff()
            return summary
        else:
            return raw_text


# ========== PHẦN TEST ==========
if __name__ == "__main__":
    print("=" * 60)
    print("TEST RESEARCHER AGENT")
    print("=" * 60)

    agent_raw = ResearcherAgent(use_llm_summary=False)

    test_requests = [
        "What is a User Story?",
        "Add Google login using OAuth",
        "Split a large payment feature"
    ]

    for req in test_requests:
        print(f"\n--- REQUEST: {req} ---")
        result = agent_raw.run(req, k=2)
        print(f"CONTEXT:\n{result[:500]}{'...' if len(result) > 500 else ''}")
        print("-" * 60)