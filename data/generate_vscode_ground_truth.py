import os
import sys
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from openai import OpenAI
except ImportError:
    print("Vui lòng cài đặt openai: pip install openai")
    sys.exit(1)

DATASET_FILE = r"d:\Antigravity\AI_Agent_PM_PRJ\data\vscode_closed_dataset.json"
OUTPUT_FILE = r"d:\Antigravity\AI_Agent_PM_PRJ\data\ai_planner_output.json"
ENV_FILE = r"d:\Antigravity\AI_Agent_PM_PRJ\src\ai_scrum_master\.env"

API_KEYS = []
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("OPENROUTER_API_KEY"):
                val = line.split("=", 1)[1].strip()
                if "," in val:
                    API_KEYS.extend([k.strip() for k in val.split(",") if k.strip()])
                elif val:
                    API_KEYS.append(val)

if not API_KEYS:
    API_KEYS = [os.environ.get("OPENROUTER_API_KEY", "")]

MODEL_NAME = "pm-agent"

PROMPT_TEMPLATE = """
You are an expert Technical Product Manager. Analyze the following GitHub issue for VSCode.

Issue Title: {title}
Issue Body: {body}

Please generate the tasks and acceptance criteria to resolve this issue as if you are planning the sprint.
1. Write a brief User Story.
2. List the Acceptance Criteria (AC).
3. List the Sub-tasks, specifying which team (Frontend/Backend) should do what.

Output strictly a JSON object:
{{
  "user_story": "...",
  "acceptance_criteria": ["..."],
  "sub_tasks": ["..."]
}}
"""

def get_client(key):
    return OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    )

def process_issue(item, index, total):
    title = item.get("input", {}).get("title", "")
    body = item.get("input", {}).get("body", "")
    issue_id = item.get("id", "")
    
    prompt = PROMPT_TEMPLATE.format(title=title, body=body)
    
    retry_count = 0
    max_retries = 3
    
    result_data = {
        "id": issue_id,
        "ai_output": {}
    }
    
    while retry_count < max_retries:
        client = get_client("ollama")
        
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1000
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
                
            pred = json.loads(content)
            result_data["ai_output"] = pred
            
            print(f"[{index+1}/{total}] Processed AI Planner output for {issue_id}")
            return result_data
            
        except Exception as e:
            print(f"Error for {issue_id}: {e}. Retrying...")
            time.sleep(2)
            retry_count += 1
            
    print(f"[{index+1}/{total}] Failed to process {issue_id}")
    return result_data

def main():
    print(f"Reading dataset from {DATASET_FILE}")
    with open(DATASET_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    data = data[:40] # Giới hạn 40 mẫu theo yêu cầu
        
    total = len(data)
    print(f"Loaded {total} issues. Generating AI Ground Truth...")
    
    results = []
    
    # Use max_workers=1 for local Ollama to avoid overloading
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = [executor.submit(process_issue, item, i, total) for i, item in enumerate(data)]
        for future in as_completed(futures):
            results.append(future.result())
            
    # Write to output file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"\nDone! Generated ground truth saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
