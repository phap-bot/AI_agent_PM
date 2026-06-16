from __future__ import annotations

import json
import re

from ai_scrum_master.core.config.settings import get_settings
from ai_scrum_master.core.utils.logging import get_logger

logger = get_logger(__name__)


class TechClassifierAgent:
    def __init__(self, llm=None) -> None:
        self.settings = get_settings()
        self.llm = llm

    def run(self, requirement: str, route: dict) -> dict:
        """Classify the requirement to extract tech_stack, domain, and search_keywords."""
        from ai_scrum_master.core.llm.setup import build_llm
        if not self.llm:
            # We can use researcher_model or reasoning_model.
            # Using researcher_model to be consistent with previous logic.
            self.llm = build_llm(model=f"ollama/{self.settings.researcher_model}", temperature=0.2)
            
        prompt = f"""You are an expert technical product manager. Analyze the following requirement to extract key information for vector database retrieval and planning.
Requirement: {requirement}

Output in strict JSON format with the following keys:
- "domain": The core domain or feature area (e.g., "auth", "payment", "user_profile").
- "tech_stack": Likely technologies involved (e.g., "react", "fastapi", "postgres").
- "search_keywords": A list of highly relevant, specific keywords for vector search.

Do not output anything other than JSON.
"""
        try:
            response = self.llm.call([{"role": "user", "content": prompt}])
            text = str(response)
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if match:
                text = match.group(0)
            logger.info("LLM trace tech classification: %s", text)
            return json.loads(text)
        except Exception as e:
            logger.warning("Tech classification failed: %s", e)
            return {"domain": "", "tech_stack": "", "search_keywords": []}
