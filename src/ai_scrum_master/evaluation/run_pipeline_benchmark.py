import json
import os
import sys

# Ensure the src directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.ai_scrum_master.core.pipeline.orchestrator import generate_story_pipeline

DATASET_FILE = r"d:\Antigravity\AI_Agent_PM_PRJ\data\vscode_closed_dataset.json"
OUTPUT_FILE = r"d:\Antigravity\AI_Agent_PM_PRJ\data\ai_planner_output.json"

def main():
    os.environ["ENABLE_LLM_LOGGING"] = "1"
    print(f"Reading dataset from {DATASET_FILE}")
    with open(DATASET_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    total = len(data)
    print(f"Loaded {total} issues. Running through PM Agent Pipeline (with RAG)...")
    
    results = []
    processed_ids = set()
    
    if os.path.exists(OUTPUT_FILE):
        print(f"Found existing {OUTPUT_FILE}, loading processed items to resume...")
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            try:
                results = json.load(f)
                processed_ids = {r.get("id") for r in results if r.get("id")}
                print(f"Resuming... Skipped {len(processed_ids)} already processed items.")
            except json.JSONDecodeError:
                pass

    for i, item in enumerate(data):
        issue_id = item.get("id", "")
        if issue_id in processed_ids:
            continue
            
        title = item.get("input", {}).get("title", "")
        body = item.get("input", {}).get("body", "")
        
        requirement = f"Issue Title: {title}\nIssue Body: {body}\n\nPlease generate tasks and acceptance criteria."
        
        print(f"[{i+1}/{total}] Processing issue {issue_id} via full pipeline...")
        
        try:
            # Chạy qua full graph pipeline, sẽ tự động Query DB và gọi PM Agent (Ollama)
            state = generate_story_pipeline(requirement=requirement, n_results=5)
            
            # Lấy context từ researcher
            rag_context = ""
            if "raw_context" in state:
                rag_context = state["raw_context"].get("results_text", "")
            elif "selected_context" in state:
                rag_context = str(state["selected_context"])
                
            # Lấy output từ planner
            planner_output = state.get("planner_output", {})
            if hasattr(planner_output, "model_dump"):
                planner_output = planner_output.model_dump()
                
            # Lưu lại format tương thích với evaluator
            result_data = {
                "id": issue_id,
                "ai_output": planner_output,
                "rag_context": rag_context
            }
            results.append(result_data)
            print(f"[{i+1}/{total}] Success for {issue_id}")
            
        except Exception as e:
            print(f"[{i+1}/{total}] Pipeline error for {issue_id}: {e}")
            result_data = {
                "id": issue_id,
                "ai_output": {},
                "rag_context": f"Error: {e}"
            }
            results.append(result_data)
            
        # Save incrementally to avoid data loss
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
    print(f"Done! Pipeline output saved to {OUTPUT_FILE}")
    print("Bạn có thể chạy script merge_for_evaluation.py và llm_judge_evaluator.py ngay bây giờ!")

if __name__ == "__main__":
    main()
