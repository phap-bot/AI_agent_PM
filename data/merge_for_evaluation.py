import json

dataset_path = "d:/Antigravity/AI_Agent_PM_PRJ/data/vscode_closed_dataset.json"
ground_truth_path = "d:/Antigravity/AI_Agent_PM_PRJ/data/vscode_real_groundtruth.json"
ai_output_path = "d:/Antigravity/AI_Agent_PM_PRJ/data/ai_planner_output.json"
eval_input_path = "d:/Antigravity/AI_Agent_PM_PRJ/data/eval_input.json"

def main():
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
    except Exception as e:
        print(f"Error loading {dataset_path}: {e}")
        return
        
    try:
        with open(ground_truth_path, 'r', encoding='utf-8') as f:
            ground_truth = json.load(f)
    except Exception as e:
        print(f"Error loading {ground_truth_path}: {e}")
        return
        
    try:
        with open(ai_output_path, 'r', encoding='utf-8') as f:
            ai_output = json.load(f)
    except Exception as e:
        print(f"Error loading {ai_output_path}: {e}")
        return

    # Create dictionaries for fast lookup
    gt_map = {item['id']: item for item in ground_truth}
    ai_map = {item['id']: item for item in ai_output}

    eval_input = []
    
    for issue in dataset:
        issue_id = issue['id']
        if issue_id not in ai_map:
            continue
            
        issue_text = f"Title: {issue['input']['title']}\nBody: {issue['input']['body']}"
        
        gt = gt_map.get(issue_id, {})
        gt_text = f"Expected Modules: {json.dumps(gt.get('expected_modules', []))}\nExpected Behaviors: {json.dumps(gt.get('expected_behaviors', []))}"
        
        ai_data = ai_map.get(issue_id, {}).get('ai_output', {})
        ai_text = json.dumps(ai_data, indent=2)
        
        rag_context = ai_map.get(issue_id, {}).get('rag_context', "No context retrieved")
        
        eval_item = {
            "id": issue_id,
            "issue_text": issue_text,
            "ground_truth": gt_text,
            "rag_context": rag_context,
            "ai_output": ai_text
        }
        eval_input.append(eval_item)
        
    with open(eval_input_path, 'w', encoding='utf-8') as f:
        json.dump(eval_input, f, indent=2, ensure_ascii=False)
        
    print(f"Merged {len(eval_input)} items into {eval_input_path}")

if __name__ == "__main__":
    main()
