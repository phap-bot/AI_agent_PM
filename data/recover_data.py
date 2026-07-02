import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai_scrum_master.core.utils.database import DatabaseManager

DATASET_FILE = r"d:\Antigravity\AI_Agent_PM_PRJ\data\vscode_closed_dataset.json"
OUTPUT_FILE = r"d:\Antigravity\AI_Agent_PM_PRJ\data\ai_planner_output.json"

def main():
    print("Loading original dataset to map requirements back to IDs...")
    with open(DATASET_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)[:40]
        
    req_to_id = {}
    for item in data:
        title = item.get("input", {}).get("title", "")
        body = item.get("input", {}).get("body", "")
        req = f"Issue Title: {title}\nIssue Body: {body}\n\nPlease generate tasks and acceptance criteria."
        req_to_id[req.strip()] = item.get("id")
        
    print("Fetching last 40 history items from MongoDB...")
    history = DatabaseManager.get_history(limit=40)
    
    results = []
    
    for record in history:
        req = record.get("requirement", "").strip()
        issue_id = req_to_id.get(req)
        
        if not issue_id:
            for k, v in req_to_id.items():
                if k[:50] == req[:50]:
                    issue_id = v
                    break
                    
        if not issue_id:
            print("Could not match requirement to issue ID, skipping.")
            continue
            
        state = record.get("result", {})
        
        story = state.get("story", {})
        context = state.get("context", {})
        rag_context = context.get("results_text", "")
        
        result_data = {
            "id": issue_id,
            "ai_output": story,
            "rag_context": rag_context
        }
        results.append(result_data)
        
    print(f"Recovered {len(results)} items from DB!")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
