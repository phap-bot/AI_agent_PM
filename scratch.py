from ai_scrum_master.agents.planner import PlannerAgent
from ai_scrum_master.core.config import AgentProfileConfig, TaskProfileConfig

def test():
    profile = AgentProfileConfig(name="planner", role="Planner", goal="Plan stories", backstory="You plan stories")
    task_profile = TaskProfileConfig(name="planner", description="Plan story", expected_output="JSON")
    agent = PlannerAgent(use_llm=True, profile=profile, task_profile=task_profile)
    req = "As a customer service representative, I want to manage customer requests efficiently so that we can improve efficiency and visibility for both customers and staff."
    context = {"documents": ["Customer requests need BE APIs for CRUD, FE interfaces for the representative dashboard, and comprehensive QA testing."]}
    output = agent.run(requirement=req, context=context)
    print("STORY POINTS:", output.get("story_points"))
    print("TASKS:", output.get("tasks"))

if __name__ == "__main__":
    test()
