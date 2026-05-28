from ai_scrum_master.agents.crew import build_scrum_master_crew
from ai_scrum_master.agents.researcher import ResearcherAgent
from ai_scrum_master.core.agent_schemas import EvaluationOutput, PlannerStoryOutput, ResearchContextOutput


def test_build_scrum_master_crew_uses_sequential_process() -> None:
    crew = build_scrum_master_crew("Add Google login", n_results=3, verbose=False)

    assert len(crew.agents) == 3
    assert len(crew.tasks) == 3
    assert crew.process == "sequential"


def test_crewai_tasks_use_context_and_structured_outputs() -> None:
    crew = build_scrum_master_crew("Add Google login", n_results=3, verbose=False)
    research_task, planning_task, evaluation_task = crew.tasks

    assert getattr(planning_task, "context", None) == [research_task]
    assert getattr(evaluation_task, "context", None) == [research_task, planning_task]
    assert getattr(research_task, "output_pydantic", None) is ResearchContextOutput
    assert getattr(planning_task, "output_pydantic", None) is PlannerStoryOutput
    assert getattr(evaluation_task, "output_pydantic", None) is EvaluationOutput


def test_researcher_agent_has_rag_tool() -> None:
    agent = ResearcherAgent().create_agent()
    tools = getattr(agent, "tools", [])

    assert tools
    assert any(getattr(tool, "name", "") == "project_context_rag_search" for tool in tools)
