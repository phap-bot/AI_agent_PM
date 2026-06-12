"""
Manual Research Testing Tool

Test the RAG pipeline by passing a raw requirement and inspecting retrieved context.

Usage:
    python scripts/test_manual_research.py -r "Add Google login"
    python scripts/test_manual_research.py -i
"""

import argparse
import sys
import os
from typing import Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai_scrum_master.agents.researcher import ResearcherAgent
from ai_scrum_master.core.logging import get_logger

logger = get_logger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Manual test utility for ResearcherAgent (RAG pipeline).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-r', '--requirement', type=str, help="Requirement text to test.")
    group.add_argument('-i', '--interactive', action='store_true', help="Interactive prompt mode.")
    parser.add_argument('-n', '--n-results', type=int, default=3, help="Number of context docs.")
    return parser.parse_args()


def display_results(requirement: str, result: dict[str, Any]) -> None:
    """Format and display retrieval results."""
    print(f"\n{'=' * 80}")
    print(f"  RAG PIPELINE RESULT")
    print(f"  Requirement : {requirement}")
    print(f"  Status      : {result.get('retrieval_status', 'Unknown').upper()}")
    print(f"{'=' * 80}")
    print(f"  Confidence  : {result.get('confidence', 0.0):.2f}")
    print(f"  Raw Matches : {result.get('raw_match_count', 0)}")
    print(f"  Filtered    : {len(result.get('documents', []))} documents")

    sources = result.get("retrieved_sources", [])
    if not sources:
        print(f"\n  No relevant context found in the knowledge base.")
        return

    print(f"\n  RETRIEVED SOURCES:")
    for index, source in enumerate(sources, 1):
        file_name = source.get('source', 'Unknown')
        score = source.get('score', 0.0)
        excerpt = source.get('excerpt', '').strip()
        display_excerpt = excerpt if len(excerpt) <= 300 else f"{excerpt[:300]}..."
        print(f"\n  [{index}] Source: {file_name} (Score: {score:.2f})")
        print(f"      {display_excerpt}")
    print(f"\n{'=' * 80}")


def execute_research(requirement: str, n_results: int) -> None:
    """Execute the ResearcherAgent with the given requirement."""
    try:
        print(f"\n  Analyzing requirement and fetching context...")
        researcher = ResearcherAgent()
        result = researcher.run(requirement=requirement, n_results=n_results)
        display_results(requirement, result)
    except Exception as exc:
        logger.exception("Research execution failed.")
        print(f"\n  Error: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Entry point."""
    args = parse_arguments()
    if args.interactive:
        print("Interactive Mode. Type 'exit' or 'quit' to stop.")
        while True:
            try:
                requirement = input("\nEnter requirement: ").strip()
                if requirement.lower() in ('exit', 'quit'):
                    break
                if requirement:
                    execute_research(requirement, args.n_results)
                else:
                    print("  Requirement cannot be empty.")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                break
    else:
        execute_research(args.requirement, args.n_results)


if __name__ == "__main__":
    main()
