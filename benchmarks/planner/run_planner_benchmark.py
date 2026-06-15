import json
import argparse
import logging
from pathlib import Path
from tqdm import tqdm
import pandas as pd

from ai_scrum_master.agents.planner import PlannerAgent
from ai_scrum_master.evaluation.planner_metrics import (
    evaluate_story_point_error,
    evaluate_classification,
    evaluate_coverage,
    evaluate_completeness,
    evaluate_breakdown_quality
)
from ai_scrum_master.core.llm_setup import build_llm
from ai_scrum_master.core.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run Benchmark for Planner Agent")
    parser.add_argument("--limit", type=int, default=3, help="Number of issues to evaluate")
    parser.add_argument("--input", type=str, default="benchmarks/planner/apache_jira_issues_50.jsonl", help="Dataset file")
    parser.add_argument("--output", type=str, default="benchmarks/planner/benchmark_report.csv", help="Output report file")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    # Load data
    dataset = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                dataset.append(json.loads(line))
                
    dataset = dataset[:args.limit]
    logger.info(f"Loaded {len(dataset)} issues for benchmarking.")

    # Initialize Agents and Judge LLM
    logger.info("Initializing Planner Agent and Judge LLM...")
    planner = PlannerAgent()
    planner.create_agent()
    
    settings = get_settings()
    judge_llm = build_llm(model=f"ollama/{settings.researcher_model}", temperature=0.0)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    results = []
    processed_ids = set()
    if out_path.exists():
        try:
            existing_df = pd.read_csv(out_path)
            if not existing_df.empty and "issue_id" in existing_df.columns:
                results = existing_df.to_dict(orient="records")
                processed_ids = set(existing_df["issue_id"].astype(str))
                logger.info(f"Resuming benchmark: Found {len(processed_ids)} already processed issues in {out_path}.")
        except Exception as e:
            logger.warning(f"Could not read existing output file {out_path}: {e}")

    for issue in tqdm(dataset, desc="Benchmarking"):
        issue_id = str(issue.get("id", "Unknown"))
        if issue_id in processed_ids:
            logger.info(f"Skipping already processed Issue: {issue_id}")
            continue
            
        summary = issue.get("summary", "")
        description = issue.get("description", "")
        parent = issue.get("parent")
        subtasks = issue.get("subtasks", [])
        links = issue.get("issuelinks", [])
        actual_sp = issue.get("story_points")
        actual_type = issue.get("issue_type")
        
        requirement = f"Title: {summary}"
        
        context_sources = []
        if description:
            context_sources.append({"source": "Jira Description", "excerpt": description, "score": 1.0, "chunk_index": 0})
        if parent:
            context_sources.append({"source": "Parent Epic", "excerpt": parent, "score": 1.0, "chunk_index": 0})
        if subtasks:
            context_sources.append({"source": "Subtasks", "excerpt": ", ".join(subtasks), "score": 1.0, "chunk_index": 0})
        if links:
            links_str = "\n".join([f"- {l.get('type')}: {l.get('outwardIssue') or l.get('inwardIssue')}" for l in links])
            context_sources.append({"source": "Issue Links", "excerpt": links_str, "score": 1.0, "chunk_index": 0})
            
        planner_context = {
            "route": {"domain": "benchmark_case"},
            "selected_context_sources": context_sources,
            "retrieved_sources": context_sources,
            "documents": [src["excerpt"] for src in context_sources],
            "context_snippets": [f"source={src['source']} chunk={src['chunk_index']} score={src['score']}: {src['excerpt']}" for src in context_sources],
            "retrieval_status": "ok"
        }
            
        logger.info(f"\nEvaluating Issue: {issue_id} - {summary[:50]}...")
        
        # 1. Run Planner
        try:
            planner_output = planner.run(requirement=requirement, context=planner_context)
        except Exception as e:
            logger.error(f"Planner failed for {issue_id}: {e}")
            continue
            
        predicted_sp = planner_output.get("story_points")
        predicted_type = planner_output.get("jira_issue_type")
        
        tasks_dict = planner_output.get("tasks", {})
        flat_tasks = []
        for group, t_list in tasks_dict.items():
            flat_tasks.extend(t_list)
        generated_tasks_str = "\n".join(f"- [{group}] {t}" for group, t_list in tasks_dict.items() for t in t_list)

        # 2. Evaluate Metrics
        sp_error = evaluate_story_point_error(predicted_sp, actual_sp) if actual_sp else None
        class_score = evaluate_classification(predicted_type, actual_type)
        
        coverage_res = evaluate_coverage(judge_llm, requirement, generated_tasks_str)
        completeness_res = evaluate_completeness(judge_llm, requirement, generated_tasks_str)
        breakdown_res = evaluate_breakdown_quality(judge_llm, generated_tasks_str)

        row = {
            "issue_id": issue_id,
            "actual_type": actual_type,
            "predicted_type": predicted_type,
            "classification_score": class_score,
            "actual_sp": actual_sp,
            "predicted_sp": predicted_sp,
            "sp_error": sp_error,
            "num_tasks_generated": len(flat_tasks),
            "coverage_score": coverage_res.score,
            "coverage_reasoning": coverage_res.reasoning,
            "completeness_score": completeness_res.score,
            "completeness_reasoning": completeness_res.reasoning,
            "breakdown_score": breakdown_res.score,
            "breakdown_reasoning": breakdown_res.reasoning,
            "status": planner_output.get("planning_status")
        }
        results.append(row)

        # Cập nhật file CSV liên tục để không mất data nếu dừng giữa chừng
        df_temp = pd.DataFrame(results)
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_temp.to_csv(out_path, index=False, encoding="utf-8-sig")

        # Save raw data for fine-tuning if planning was successful
        if planner_output.get("planning_status") == "READY" and coverage_res.score >= 0.8:
            raw_data_path = out_path.parent / f"{out_path.stem}_raw.jsonl"
            fine_tune_record = {
                "issue_id": issue_id,
                "requirement": requirement,
                "context": planner_context,
                "planner_output": planner_output,
                "metrics": {
                    "coverage_score": coverage_res.score,
                    "completeness_score": completeness_res.score,
                    "breakdown_score": breakdown_res.score
                }
            }
            with open(raw_data_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(fine_tune_record, ensure_ascii=False) + "\n")

    logger.info(f"\nBenchmark completed! Report saved to {out_path}")
    
    # Print summary
    df = pd.DataFrame(results)
    logger.info("\n--- Benchmark Summary ---")
    logger.info(f"Total Evaluated: {len(df)}")
    logger.info(f"Avg Classification Score: {df['classification_score'].mean():.2f}")
    if df["sp_error"].notna().any():
        logger.info(f"Avg Story Point Error (MAE): {df['sp_error'].mean():.2f}")
    logger.info(f"Avg Coverage Score: {df['coverage_score'].mean():.2f}")
    logger.info(f"Avg Completeness Score: {df['completeness_score'].mean():.2f}")
    logger.info(f"Avg Breakdown Quality Score: {df['breakdown_score'].mean():.2f}")

if __name__ == "__main__":
    main()
