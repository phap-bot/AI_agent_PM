"""
RAG Quality Check -- Task 3 (W3-4 Phuc)
=========================================
Chay 20 cau query test qua pipeline ChromaDB va do cac metrics:
  - Hit Rate@K: ty le queries co it nhat 1 relevant result trong top-K
  - Recall@K:   ty le expected sources duoc tim thay trong top-K
  - MRR:        vi tri trung binh cua relevant result dau tien
  - NDCG@K:     normalized discounted cumulative gain

Cach chay:
    cd c:\\AI_agent_PM_Phap
    .venv\\Scripts\\Activate.ps1
    $env:PYTHONPATH = "src"
    python -m ai_scrum_master.evaluation.rag_quality_check
"""
from __future__ import annotations

import sys
import json
from pathlib import Path
from typing import Any

# Force UTF-8 output on Windows to avoid cp1252 UnicodeEncodeError
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ---------------------------------------------------------------------------
# 20 Test Queries — đa dạng domain: auth, checkout, notification, scrum, agile
# ---------------------------------------------------------------------------
QUERY_CASES: list[dict[str, Any]] = [
    # --- AUTH (6 queries) ---
    {
        "id": "Q01",
        "domain": "auth",
        "query": "Add Google login using OAuth for existing users",
        "expected_sources": ["auth_context.md"],
    },
    {
        "id": "Q02",
        "domain": "auth",
        "query": "JWT token refresh endpoint backend implementation",
        "expected_sources": ["auth_context.md"],
    },
    {
        "id": "Q03",
        "domain": "auth",
        "query": "User logout from authenticated routes",
        "expected_sources": ["auth_context.md"],
    },
    {
        "id": "Q04",
        "domain": "auth",
        "query": "OAuth callback code exchange server-side",
        "expected_sources": ["auth_context.md"],
    },
    {
        "id": "Q05",
        "domain": "auth",
        "query": "Show error when Google authentication is cancelled",
        "expected_sources": ["auth_context.md"],
    },
    {
        "id": "Q06",
        "domain": "auth",
        "query": "Prevent access tokens from appearing in URL query parameters",
        "expected_sources": ["auth_context.md"],
    },
    # --- CHECKOUT (5 queries) ---
    {
        "id": "Q07",
        "domain": "checkout",
        "query": "Payment retry without creating duplicate orders",
        "expected_sources": ["checkout_context.md"],
    },
    {
        "id": "Q08",
        "domain": "checkout",
        "query": "Show retry message when payment provider times out",
        "expected_sources": ["checkout_context.md"],
    },
    {
        "id": "Q09",
        "domain": "checkout",
        "query": "Block order creation when inventory mismatch",
        "expected_sources": ["checkout_context.md"],
    },
    {
        "id": "Q10",
        "domain": "checkout",
        "query": "Apply discount coupon validation at checkout",
        "expected_sources": ["checkout_context.md"],
    },
    {
        "id": "Q11",
        "domain": "checkout",
        "query": "Backend calculates shipping fee and tax for order",
        "expected_sources": ["checkout_context.md"],
    },
    # --- NOTIFICATION (3 queries) ---
    {
        "id": "Q12",
        "domain": "notification",
        "query": "Send Slack alert when Jira creation fails",
        "expected_sources": ["notification_context.md"],
    },
    {
        "id": "Q13",
        "domain": "notification",
        "query": "Email notification for customer-facing workflow events",
        "expected_sources": ["notification_context.md"],
    },
    {
        "id": "Q14",
        "domain": "notification",
        "query": "Block Slack notification when evaluator status is REVISION",
        "expected_sources": ["notification_context.md"],
    },
    # --- SCRUM / AGILE (4 queries) ---
    {
        "id": "Q15",
        "domain": "scrum",
        "query": "Write user story with acceptance criteria Given When Then",
        "expected_sources": ["sprint_policy.md"],
    },
    {
        "id": "Q16",
        "domain": "scrum",
        "query": "Sprint Planning story points Fibonacci estimation",
        "expected_sources": ["sprint_policy.md"],
    },
    {
        "id": "Q17",
        "domain": "scrum",
        "query": "Split oversized requirement into multiple user stories across sprints",
        "expected_sources": ["sprint_policy.md"],
    },
    {
        "id": "Q18",
        "domain": "scrum",
        "query": "Clarification questions for ambiguous requirements",
        "expected_sources": ["sprint_policy.md"],
    },
    # --- CROSS-DOMAIN (2 queries) ---
    {
        "id": "Q19",
        "domain": "cross",
        "query": "User must be authenticated before accessing checkout payment",
        "expected_sources": ["auth_context.md", "checkout_context.md"],
    },
    {
        "id": "Q20",
        "domain": "cross",
        "query": "Improve sprint planning process with automated story generation",
        "expected_sources": ["sprint_policy.md"],
    },
    # --- ADDITIONAL GROUND TRUTH (10 queries: Q21-Q30) ---
    # Auth — deeper scenarios
    {
        "id": "Q21",
        "domain": "auth",
        "query": "Map Google email to existing user or create pending user record",
        "expected_sources": ["auth_context.md"],
    },
    {
        "id": "Q22",
        "domain": "auth",
        "query": "Unit tests for token handling and callback validation",
        "expected_sources": ["auth_context.md"],
    },
    # Checkout — deeper scenarios
    {
        "id": "Q23",
        "domain": "checkout",
        "query": "Cart review and shipping address before payment confirmation",
        "expected_sources": ["checkout_context.md"],
    },
    {
        "id": "Q24",
        "domain": "checkout",
        "query": "Frontend displays totals returned by backend pricing API",
        "expected_sources": ["checkout_context.md"],
    },
    # Notification — deeper scenarios
    {
        "id": "Q25",
        "domain": "notification",
        "query": "In-app notification for user dashboard events",
        "expected_sources": ["notification_context.md"],
    },
    {
        "id": "Q26",
        "domain": "notification",
        "query": "Slack message must include title story points and Jira reference",
        "expected_sources": ["notification_context.md"],
    },
    # Sprint/Scrum — deeper scenarios
    {
        "id": "Q27",
        "domain": "scrum",
        "query": "Jira issues must not be created before evaluator status APPROVED",
        "expected_sources": ["sprint_policy.md"],
    },
    {
        "id": "Q28",
        "domain": "scrum",
        "query": "Each story must be independently deliverable and testable",
        "expected_sources": ["sprint_policy.md"],
    },
    # Cross-domain — new combinations
    {
        "id": "Q29",
        "domain": "cross",
        "query": "Notify team on Slack after successful checkout order creation",
        "expected_sources": ["notification_context.md", "checkout_context.md"],
    },
    {
        "id": "Q30",
        "domain": "cross",
        "query": "QA test plan for login callback and payment failure scenarios",
        "expected_sources": ["auth_context.md", "checkout_context.md"],
    },
]

K = 3  # top-K for evaluation


def normalize_source(source: str) -> str:
    """Normalize source path to filename only."""
    return Path(source.replace("\\", "/")).name.lower()


def run_quality_check(k: int = K) -> dict[str, Any]:
    """Run all 20 queries and compute aggregate metrics."""
    try:
        from ai_scrum_master.core.quality_gate import evaluate_retrieval_cases
    except ImportError as exc:
        print(f"[ERROR] Cannot import quality gate: {exc}", file=sys.stderr)
        print("Make sure PYTHONPATH=src and dependencies are installed.", file=sys.stderr)
        sys.exit(1)

    # Build cases format expected by evaluate_retrieval_cases
    cases = [
        {
            "query": case["query"],
            "expected_sources": case["expected_sources"],
        }
        for case in QUERY_CASES
    ]

    print(f"\n{'='*60}")
    print("  RAG Quality Check — W3-4 Phuc")
    print(f"  Queries: {len(cases)} | Top-K: {k}")
    print(f"{'='*60}\n")

    results = evaluate_retrieval_cases(cases, k=k)
    agg = results["aggregate"]

    # Print per-query results
    print(f"{'ID':<5} {'Domain':<14} {'HR':<6} {'Rec':<6} {'MRR':<6} {'NDCG':<6}  Query")
    print("-" * 80)
    for i, (case, qr) in enumerate(zip(QUERY_CASES, results["queries"])):
        hr   = "[OK]" if qr["hit_rate_at_k"] == 1.0 else "[--]"
        rec  = f"{qr['recall_at_k']:.2f}"
        mrr  = f"{qr['mrr']:.2f}"
        ndcg = f"{qr['ndcg_at_k']:.2f}"
        print(f"{case['id']:<5} {case['domain']:<14} {hr:<6} {rec:<6} {mrr:<6} {ndcg:<6}  {case['query'][:45]}")

    # Print aggregate
    print(f"\n{'='*60}")
    print("  AGGREGATE METRICS")
    print(f"{'='*60}")
    print(f"  Hit Rate@{k}:   {agg['hit_rate_at_k']:.4f}  (target: >= 0.80)")
    print(f"  Recall@{k}:     {agg['recall_at_k']:.4f}  (target: >= 0.70)")
    print(f"  Precision@{k}:  {agg['precision_at_k']:.4f}  (target: >= 0.50)")
    print(f"  MRR:           {agg['mrr']:.4f}  (target: >= 0.70)")
    print(f"  NDCG@{k}:       {agg['ndcg_at_k']:.4f}  (target: >= 0.70)")

    # Pass/fail per metric
    thresholds = {
        "hit_rate_at_k": 0.80, "recall_at_k": 0.70,
        "precision_at_k": 0.50, "mrr": 0.70, "ndcg_at_k": 0.70,
    }
    passed_all = all(agg.get(m, 0) >= t for m, t in thresholds.items())
    gate_label = "[PASSED]" if passed_all else "[FAILED]"
    print(f"\n  Overall Quality Gate: {gate_label}")

    # Per-source breakdown
    print(f"\n{'='*60}")
    print("  PER-SOURCE RECALL")
    print(f"{'='*60}")
    for source, metrics in sorted(results["per_source"].items()):
        recall = metrics["recall_at_k"]
        status = "[OK]" if recall >= 0.7 else "[--]"
        print(f"  {status} {source:<35} recall@{k}={recall:.2f}  ({metrics['hit_queries']}/{metrics['expected_queries']} queries hit)")

    # Save JSON report
    report = {
        "k": k,
        "queries": len(cases),
        "aggregate": agg,
        "per_source": results["per_source"],
        "query_results": [
            {
                "id": case["id"],
                "domain": case["domain"],
                "query": case["query"],
                "expected_sources": case["expected_sources"],
                "hit_rate": qr["hit_rate_at_k"],
                "recall": qr["recall_at_k"],
                "mrr": qr["mrr"],
                "ndcg": qr["ndcg_at_k"],
                "found_sources": qr.get("found_sources", []),
            }
            for case, qr in zip(QUERY_CASES, results["queries"])
        ],
        "passed": passed_all,
    }
    report_path = Path(__file__).parent / "rag_quality_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  [Report saved] {report_path}")
    print(f"{'='*60}\n")

    return report


if __name__ == "__main__":
    run_quality_check(k=K)
