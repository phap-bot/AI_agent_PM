"""
End-to-end Full Pipeline test voi Ollama LLM thuc.
Test pipeline: requirement -> ResearcherAgent -> PlannerAgent -> EvaluatorAgent -> APPROVED/REVISION

Chay:
    .\.venv\Scripts\Activate.ps1
    $env:PYTHONPATH = "src"
    python scripts/test_pipeline_e2e.py
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, 'src')

from ai_scrum_master.agents.researcher import ResearcherAgent
from ai_scrum_master.agents.planner import PlannerAgent
from ai_scrum_master.agents.evaluator import EvaluatorAgent
from ai_scrum_master.core.config import get_settings

TEST_REQUIREMENTS = [
    "Add Google login using OAuth so that users can sign in with their Google account",
    "Implement retry-safe checkout payment so that duplicate orders are prevented",
    "Write sprint planning user story with Given When Then acceptance criteria",
]

def main() -> None:
    settings = get_settings()
    print(f"\nOllama: {settings.ollama_base_url}")
    print(f"LLM model: {settings.reasoning_model}")
    print(f"Embed model: {settings.embedding_model}")

    researcher = ResearcherAgent()
    planner = PlannerAgent()
    evaluator = EvaluatorAgent()

    results = []
    for req in TEST_REQUIREMENTS:
        print(f"\n{'='*70}")
        print(f"REQUIREMENT: {req}")
        print(f"{'='*70}")
        
        print(f"\n[1/3] RESEARCHING...")
        research = researcher.run(req, n_results=3)
        status = research.get('retrieval_status', '?')
        confidence = research.get('confidence', 0)
        docs = len(research.get('documents', []))
        print(f"  -> retrieval_status={status}, confidence={confidence:.2f}, docs={docs}")

        print(f"\n[2/3] PLANNING...")
        story = planner.run(requirement=req, context=research)
        print(f"  -> title: {story.get('title')}")
        print(f"  -> status: {story.get('planning_status')}")
        ac_count = len(story.get('acceptance_criteria', []))
        print(f"  -> AC count: {ac_count}")
        print(f"  -> Story points: {story.get('story_points')}")
        print(f"  -> Latency: {story.get('latency_ms', 0)}ms")

        print(f"\n[3/3] EVALUATING...")
        evaluation = evaluator.run(story=story)
        print(f"  -> Status: {evaluation.get('status')}")
        
        issues = evaluation.get('issues', [])
        if issues:
            print(f"  -> Issues ({len(issues)}):")
            for i, issue in enumerate(issues, 1):
                print(f"     {i}. {issue}")
                
        revision_instructions = evaluation.get('revision_instructions', [])
        if revision_instructions:
            print(f"  -> Revision Instructions:")
            for i, instr in enumerate(revision_instructions, 1):
                print(f"     {i}. {instr}")

        dod_score = evaluation.get('dod_score', {})
        if dod_score:
            print(f"  -> DoD Score: {dod_score.get('score', 0)}/{dod_score.get('total', 0)}")
            
        print(f"  -> Latency: {evaluation.get('latency_ms', 0)}ms")

        results.append({
            'requirement': req,
            'retrieval_status': status,
            'planning_status': story.get('planning_status'),
            'evaluation_status': evaluation.get('status'),
            'issues_count': len(issues),
            'dod_score': f"{dod_score.get('score', 0)}/{dod_score.get('total', 0)}",
            'planner_ms': story.get('latency_ms', 0),
            'evaluator_ms': evaluation.get('latency_ms', 0),
        })

    # Summary table
    print(f"\n{'='*95}")
    print("  E2E PIPELINE SUMMARY")
    print(f"{'='*95}")
    print(f"  {'Req':<40} {'Plan Status':<15} {'Eval Status':<15} {'Issues':<8} {'DoD':<8}")
    print(f"  {'-'*90}")
    for r in results:
        req_short = r['requirement'][:38]
        print(f"  {req_short:<40} {r['planning_status']:<15} {r['evaluation_status']:<15} {r['issues_count']:<8} {r['dod_score']:<8}")

    report_path = Path('src/ai_scrum_master/evaluation/e2e_pipeline_report.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n  [Report saved] {report_path}")

if __name__ == '__main__':
    main()
