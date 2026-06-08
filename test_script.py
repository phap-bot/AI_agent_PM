import json
from ai_scrum_master.agents.planner import PlannerAgent
with open("payload.json", encoding="utf-8") as f:
    payload = json.load(f)
agent = PlannerAgent()
story = agent._normalize_story(
    story=payload,
    requirement="Customer Booking System Core Feature",
    warnings=[],
    planning_status="READY",
    context_sources=[{"excerpt": "Method Endpoint Mục đích POST /api/v1/auth/request-otp"}],
    route={"template_name": "notification", "required_concepts": ["notification_trigger", "channel"]}
)
print("Normalized Tasks:", json.dumps(story["tasks"], indent=2))
print("Warnings:", json.dumps(story["warnings"], indent=2))
