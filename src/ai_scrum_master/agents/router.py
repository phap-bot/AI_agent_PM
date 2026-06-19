from __future__ import annotations

import json
import re

from ai_scrum_master.core.config.settings import get_settings
from ai_scrum_master.core.utils.logging import get_logger

logger = get_logger(__name__)


class RouterAgent:
    def __init__(self, llm=None) -> None:
        self.settings = get_settings()
        self.llm = llm

    def run(self, requirement: str) -> dict:
        """Analyze the requirement to extract story_type, domain, tech_stack, and search_keywords."""
        from ai_scrum_master.core.llm.setup import build_llm
        if not self.llm:
            # We use researcher_model because it's fast enough for routing
            self.llm = build_llm(model=f"ollama/{self.settings.researcher_model}", temperature=0.1)
            
        prompt = f"""You are an expert technical product manager and Agile Scrum Master. 
Analyze the following requirement to extract key information for workflow routing and planning.
Requirement: {requirement}

Output in strict JSON format with exactly these 6 keys:
- "clarity_reasoning": Explain your evaluation of the requirement's clarity based on semantic context, not just keywords. For example, if it asks to 'optimize API', check for concrete metrics (e.g., 'response time < 200ms'). If it lacks metrics or specific context, explain why it is ambiguous.
- "scope_reasoning": Explain your evaluation of the requirement's scope. A good task can be completed by 1 dev in 1-3 days. If the requirement describes a massive feature requiring frontend, backend, DB, and 3rd-party integration, explain why the scope > 80 (oversized).
- "story_type": Must be one of ["software_feature", "process_improvement", "oversized_request", "ambiguous_request"].
  * IMPORTANT RULES for story_type:
    1. If the request is a bug fix, minor update, or single concrete feature with acceptable clarity, it is "software_feature".
    2. ONLY use "oversized_request" if your scope_reasoning concludes it's a massive Epic that MUST be split.
    3. Use "ambiguous_request" if your clarity_reasoning concludes it lacks specific metrics or is too vague to act on.
    4. Use "process_improvement" if it's about Agile/Scrum processes.
- "domain": The core business domain or feature area (e.g., "auth", "checkout", "notification", "scrum", "general").
- "tech_stack": Likely technologies involved (e.g., "react", "fastapi", "postgres").
- "search_keywords": A list of highly relevant, specific keywords for RAG vector search.

IMPORTANT: Always fill out "clarity_reasoning" and "scope_reasoning" BEFORE deciding the "story_type".
Do not output anything other than JSON.
"""
        try:
            response = self.llm.call([{"role": "user", "content": prompt}])
            text = str(response)
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if match:
                text = match.group(0)
            logger.info("LLM trace router classification: %s", text)
            result = json.loads(text)
            
            # Ensure safe fallback values
            story_type_val = result.get("story_type")
            if isinstance(story_type_val, list):
                story_type_val = story_type_val[0] if story_type_val else "software_feature"
                
            domain_val = result.get("domain")
            if isinstance(domain_val, list):
                domain_val = domain_val[0] if domain_val else "general"
                
            return {
                "story_type": str(story_type_val) if story_type_val else "software_feature",
                "domain": str(domain_val) if domain_val else "general",
                "tech_stack": result.get("tech_stack") or "",
                "search_keywords": result.get("search_keywords") or [],
                "clarity_reasoning": result.get("clarity_reasoning") or "",
                "scope_reasoning": result.get("scope_reasoning") or ""
            }
        except Exception as e:
            logger.warning("Router classification failed: %s", e)
            return {
                "story_type": "software_feature",
                "domain": "general", 
                "tech_stack": "", 
                "search_keywords": [],
                "clarity_reasoning": "",
                "scope_reasoning": ""
            }
