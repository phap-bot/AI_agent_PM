"""
End-to-end Planner Agent test voi Ollama LLM thuc.
Test pipeline: requirement -> ResearcherAgent -> PlannerAgent -> user story

Chay:
    .venv\\Scripts\\Activate.ps1
    $env:PYTHONPATH = "src"
    python scripts/test_planner_e2e.py
"""
from __future__ import annotations

import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, 'src')

from ai_scrum_master.agents.researcher import ResearcherAgent
from ai_scrum_master.agents.planner import PlannerAgent
from ai_scrum_master.core.config import get_settings

# 3 test requirements: auth, checkout, scrum
TEST_REQUIREMENTS = [
    "Add Google login using OAuth so that users can sign in with their Google account",
    "Implement retry-safe checkout payment so that duplicate orders are prevented",
    "Write sprint planning user story with Given When Then acceptance criteria",
]

def print_story(story: dict, req: str) -> None:
    print(f"\n{'='*60}")
    print(f"  REQUIREMENT: {req[:60]}")
    print(f"{'='*60}")
    print(f"  Title:          {story.get('title', '[empty]')}")
    print(f"  Status:         {story.get('planning_status', '?')}")
    print(f"  Story Type:     {story.get('story_type', '?')}")
    print(f"  Story Points:   {story.get('story_points', 'N/A')}")
    print(f"  LLM used:       {story.get('latency_ms', 0)}ms")

    user_story = story.get('user_story', '')
    if user_story:
        print(f"\n  User Story:\n    {user_story[:200]}")

    ac = story.get('acceptance_criteria', [])
    if ac:
        print(f"\n  Acceptance Criteria ({len(ac)}):")
        for i, c in enumerate(ac[:3], 1):
            print(f"    {i}. {str(c)[:100]}")

    tasks = story.get('tasks', {})
    for group in ('be', 'fe', 'qa'):
        items = tasks.get(group, [])
        if items:
            print(f"  {group.upper()} tasks: {items[0][:80]}{'...' if len(items) > 1 else ''}")

    dod = story.get('definition_of_done', [])
    if dod:
        print(f"  DoD ({len(dod)} items): {dod[0][:80]}")

    ctx = story.get('context_sources', [])
    if ctx:
        print(f"  Context sources: {[s.get('source', '?') for s in ctx[:3]]}")

    warnings = story.get('warnings', [])
    if warnings:
        print(f"  Warnings ({len(warnings)}): {warnings[0][:80]}")

    print()


def main() -> None:
    settings = get_settings()
    print(f"\nOllama: {settings.ollama_base_url}")
    print(f"LLM model: {settings.reasoning_model}")
    print(f"Embed model: {settings.embedding_model}")

    researcher = ResearcherAgent()
    planner = PlannerAgent()  # uses real Ollama LLM

    results = []
    for req in TEST_REQUIREMENTS:
        print(f"\n[RESEARCH] {req[:60]}...")
        research = researcher.run(req, n_results=3)
        status = research.get('retrieval_status', '?')
        confidence = research.get('confidence', 0)
        docs = len(research.get('documents', []))
        print(f"  -> retrieval_status={status}, confidence={confidence:.2f}, docs={docs}")

        print(f"[PLAN]     Calling PlannerAgent with LLM...")
        story = planner.run(requirement=req, context=research)
        print_story(story, req)

        results.append({
            'requirement': req,
            'retrieval_status': status,
            'planning_status': story.get('planning_status'),
            'story_type': story.get('story_type'),
            'title': story.get('title'),
            'user_story': story.get('user_story', '')[:200],
            'ac_count': len(story.get('acceptance_criteria', [])),
            'story_points': story.get('story_points'),
            'warnings_count': len(story.get('warnings', [])),
            'latency_ms': story.get('latency_ms'),
        })

    # Summary table
    print(f"\n{'='*70}")
    print("  END-TO-END SUMMARY")
    print(f"{'='*70}")
    print(f"  {'Req':<45} {'Status':<20} {'AC':<4} {'SP':<4} {'ms'}")
    print(f"  {'-'*65}")
    for r in results:
        req_short = r['requirement'][:43]
        print(f"  {req_short:<45} {r['planning_status']:<20} {r['ac_count']:<4} {str(r['story_points']):<4} {r['latency_ms']}")

    # Save report
    import json
    from pathlib import Path
    report_path = Path('src/ai_scrum_master/evaluation/e2e_planner_report.json')
    report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n  [Report saved] {report_path}")


if __name__ == '__main__':
    main()
