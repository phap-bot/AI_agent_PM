import json
from ai_scrum_master.agents.planner import PlannerAgent
from ai_scrum_master.core.llm_setup import build_llm

with open('benchmarks/planner/apache_jira_issues_50.jsonl', 'r', encoding='utf-8') as f:
    issue = json.loads(f.readlines()[1])

planner = PlannerAgent()
planner.create_agent()
res = planner.run(requirement=f"Title: {issue['summary']}\n\nDescription: {issue['description']}", context={'route': {'domain': 'benchmark_case'}})
print("TASKS:", json.dumps(res['tasks'], indent=2))
print("WARNINGS:", res['warnings'])
