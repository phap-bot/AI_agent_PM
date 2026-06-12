"""
Manual Full Pipeline Test

Test the complete pipeline: requirement -> Researcher -> Planner -> Evaluator -> Action Preview
Displays structured output for visual verification by the developer.

Usage:
    python scripts/test_manual_pipeline.py -r "Add Google login"
    python scripts/test_manual_pipeline.py -i
"""

import argparse
import json
import sys
import os
from typing import Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai_scrum_master.core.pipeline import ScrumMasterCrew
from ai_scrum_master.core.logging import get_logger

logger = get_logger(__name__)

SECTION_WIDTH = 80


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manual test: full pipeline (requirement → story → evaluation → actions).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-r', '--requirement', type=str, help="Requirement text.")
    group.add_argument('-i', '--interactive', action='store_true', help="Interactive mode.")
    parser.add_argument('-n', '--n-results', type=int, default=3, help="Context docs to retrieve.")
    return parser.parse_args()


def display_section(title: str) -> None:
    print(f"\n{'=' * SECTION_WIDTH}")
    print(f"  {title}")
    print(f"{'=' * SECTION_WIDTH}")


def display_context(result: dict[str, Any]) -> None:
    ctx = result.get("context", {})
    display_section("📚 RESEARCHER CONTEXT")
    print(f"  Status     : {ctx.get('retrieval_status', '?')}")
    print(f"  Confidence : {ctx.get('confidence', 0):.2f}")
    print(f"  Documents  : {len(ctx.get('documents', []))}")
    print(f"  Warnings   : {len(ctx.get('warnings', []))}")

    sources = ctx.get("retrieved_sources", [])
    if sources:
        print(f"\n  📑 Sources:")
        for i, s in enumerate(sources, 1):
            excerpt = s.get('excerpt', '')[:200]
            print(f"    [{i}] {s.get('source', '?')} (score={s.get('score', 0):.2f})")
            print(f"        {excerpt}")
    else:
        print(f"\n  ❌ No context retrieved.")

    for w in ctx.get("warnings", []):
        print(f"  ⚠️  {w}")


def display_story(result: dict[str, Any]) -> None:
    story = result.get("story")
    display_section("📋 PLANNER STORY")
    if not story or not isinstance(story, dict):
        print("  ❌ No story generated.")
        return

    print(f"  Title    : {story.get('title', '[empty]')}")
    print(f"  Status   : {story.get('planning_status', '?')}")
    print(f"  Type     : {story.get('story_type', '?')}")
    print(f"  Points   : {story.get('story_points', 'N/A')}")

    us = story.get('user_story', '')
    if us:
        print(f"\n  User Story:")
        print(f"    {us[:300]}")

    acs = story.get('acceptance_criteria', [])
    if acs:
        print(f"\n  Acceptance Criteria ({len(acs)}):")
        for j, ac in enumerate(acs[:5], 1):
            print(f"    {j}. {str(ac)[:150]}")

    tasks = story.get('tasks', {})
    for group in ('be', 'fe', 'qa'):
        items = tasks.get(group, [])
        if items:
            print(f"  {group.upper()} Tasks ({len(items)}): {str(items[0])[:100]}")

    dod = story.get('definition_of_done', [])
    if dod:
        print(f"\n  Definition of Done ({len(dod)}):")
        for j, d in enumerate(dod[:3], 1):
            print(f"    {j}. {d[:120]}")


def display_evaluation(result: dict[str, Any]) -> None:
    ev = result.get("evaluation", {})
    display_section("✅ EVALUATOR RESULT")
    print(f"  Status   : {ev.get('status', '?')}")

    issues = ev.get('issues', [])
    if issues:
        print(f"  Issues ({len(issues)}):")
        for issue in issues[:5]:
            print(f"    • {issue}")

    dod_score = ev.get('dod_score', {})
    if dod_score:
        print(f"  DoD Score: {dod_score.get('score', 0)}/{dod_score.get('total', 0)}")


def display_actions(result: dict[str, Any]) -> None:
    actions = result.get("actions", {})
    display_section("🚀 ACTION PREVIEW")
    for tool_name in ("jira", "slack"):
        action = actions.get(tool_name, {})
        ready = action.get("ready", False)
        icon = "✅" if ready else "⛔"
        print(f"  {icon} {tool_name.upper()}: {'Ready' if ready else 'Blocked'}")
        for w in action.get("warnings", []):
            print(f"     ⚠️  {w}")


def run_pipeline(requirement: str, n_results: int) -> None:
    try:
        print(f"\n⏳ Running full pipeline for: \"{requirement}\"...")
        crew = ScrumMasterCrew()
        result = crew.run(
            requirement=requirement,
            n_results=n_results,
            allow_fallback_without_context=True,
        )

        display_context(result)
        display_story(result)
        display_evaluation(result)
        display_actions(result)

        display_section("📊 PIPELINE SUMMARY")
        ctx = result.get("context", {})
        story = result.get("story", {}) or {}
        ev = result.get("evaluation", {})
        print(f"  Retrieval  : {ctx.get('retrieval_status', '?')} (confidence={ctx.get('confidence', 0):.2f})")
        print(f"  Planning   : {story.get('planning_status', '?') if isinstance(story, dict) else '?'}")
        print(f"  Evaluation : {ev.get('status', '?')}")
        actions = result.get("actions", {})
        print(f"  Jira       : {'Ready' if actions.get('jira', {}).get('ready') else 'Blocked'}")
        print(f"  Slack      : {'Ready' if actions.get('slack', {}).get('ready') else 'Blocked'}")
        print()

    except Exception as exc:
        logger.exception("Pipeline execution failed.")
        print(f"\n❌ Error: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    args = parse_arguments()

    if args.interactive:
        print("Interactive Mode. Type 'exit' to stop.\n")
        while True:
            try:
                requirement = input("Enter requirement: ").strip()
                if requirement.lower() in ('exit', 'quit'):
                    break
                if requirement:
                    run_pipeline(requirement, args.n_results)
                else:
                    print("⚠️  Requirement cannot be empty.")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                break
    else:
        run_pipeline(args.requirement, args.n_results)


if __name__ == "__main__":
    main()
