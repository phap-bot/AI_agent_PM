import os
import sys
import json
import time
import argparse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Xử lý tiếng Việt trên Windows Terminal
sys.stdout.reconfigure(encoding='utf-8')

try:
    from openai import OpenAI
except ImportError:
    print("Vui lòng cài đặt openai: pip install openai")
    sys.exit(1)

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

MODEL_NAME = "openai/gpt-oss-120b:free" # Hoặc "google/gemini-pro-1.5", "anthropic/claude-3.5-sonnet"

PROMPT_TEMPLATE = """
You are an expert Technical Lead and Agile Coach. Your job is to evaluate the output of an AI Project Manager against the Ground Truth.

Here is the context:

[ISSUE DESCRIPTION]
{issue_text}

[GROUND TRUTH (CODE PATCH / ACTUAL CHANGES)]
{ground_truth}

[RAG RETRIEVED CONTEXT FILES]
{rag_context}

[AI GENERATED TASKS, USER STORIES & ACCEPTANCE CRITERIA]
{ai_output}

Evaluate the AI's output on a scale of 1 to 5 for the following 4 criteria:
1. Feature Recognition (Logic & AC): Did the AI correctly understand the issue and extract the right features/logic into the User Story and Acceptance Criteria, aligning with the Ground Truth?
2. Requirement Classification (Team Assignment): Did the AI correctly identify whether the requirement needs Backend (BE), Frontend (FE), or QA effort based on the Ground Truth?
3. Domain & Type Determination: Did the AI correctly determine the business domain and requirement type (e.g., Feature, Bug, Auth, UI, Core)?
4. Task Scope Identification: Did the AI correctly identify the overall scope/intent of the task (focusing on WHAT needs to be done, rather than generating a detailed list of sub-tasks)?

*SPECIAL CASE: NEEDS CLARIFICATION*
If the AI output did not generate Stories but instead asked Clarification Questions (Needs Clarification):
- Compare the Issue Description to the Ground Truth code patch.
- If the issue is genuinely too vague and a developer would absolutely need to ask those clarifying questions before writing the patch, give a high score (4-5) across all metrics, explaining that recognizing ambiguity is correct PM behavior.
- If the issue actually contained enough info to deduce the patch, but the AI gave up, penalize the AI heavily (score 1-2).

Output ONLY a valid JSON object with exactly the following structure (no markdown wrappers like ```json):
{{
  "feature_recognition_score": <int 1-5>,
  "feature_recognition_reason": "<explanation>",
  "requirement_classification_score": <int 1-5>,
  "requirement_classification_reason": "<explanation>",
  "domain_type_score": <int 1-5>,
  "domain_type_reason": "<explanation>",
  "task_scope_score": <int 1-5>,
  "task_scope_reason": "<explanation>"
}}
"""

def get_client(key):
    return OpenAI(
        base_url="https://openrouter.ai/api/v1/chat/completions",
        api_key=key,
        timeout=120.0
    )

def evaluate_single_case(item, index, total):
    # Lấy dữ liệu từ item (có thể tùy chỉnh lại theo cấu trúc file của bạn)
    issue_id = item.get("id", f"Task-{index}")
    issue_text = item.get("issue_text", "")
    ground_truth = item.get("ground_truth", "")
    rag_context = item.get("rag_context", "No RAG context provided")
    ai_output = item.get("ai_output", "")
    
    prompt = PROMPT_TEMPLATE.format(
        issue_text=issue_text,
        ground_truth=ground_truth,
        rag_context=rag_context,
        ai_output=ai_output
    )
    
    retry_count = 0
    max_retries = len(API_KEYS) * 3 if API_KEYS else 5
    
    result_data = {
        "id": issue_id,
        "scores": {
            "feature_recognition_score": 0,
            "requirement_classification_score": 0,
            "domain_type_score": 0,
            "task_scope_score": 0
        },
        "reasons": {},
        "status": "failed"
    }
    
    while retry_count < max_retries:
        key = API_KEYS[retry_count % len(API_KEYS)]
        client = get_client(key)
        
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500
            )
            content = response.choices[0].message.content.strip()
            
            # Xử lý nếu model trả về markdown block
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
                
            pred = json.loads(content)
            
            result_data["scores"]["feature_recognition_score"] = pred.get("feature_recognition_score", 0)
            result_data["scores"]["requirement_classification_score"] = pred.get("requirement_classification_score", 0)
            result_data["scores"]["domain_type_score"] = pred.get("domain_type_score", 0)
            result_data["scores"]["task_scope_score"] = pred.get("task_scope_score", 0)
            
            result_data["reasons"] = {
                "feature_recognition_reason": pred.get("feature_recognition_reason", ""),
                "requirement_classification_reason": pred.get("requirement_classification_reason", ""),
                "domain_type_reason": pred.get("domain_type_reason", ""),
                "task_scope_reason": pred.get("task_scope_reason", "")
            }
            result_data["status"] = "success"
            
            print(f"[{index+1}/{total}] Đã chấm điểm thành công cho {issue_id}")
            return result_data
            
        except Exception as e:
            print(f"[{index+1}/{total}] Rate limit/Lỗi khi chấm điểm {issue_id}: {e}. Đang đợi 20s để thử lại...")
            time.sleep(20)
            retry_count += 1
            
    print(f"[{index+1}/{total}] THẤT BẠI khi chấm điểm {issue_id}")
    return result_data

def main():
    parser = argparse.ArgumentParser(description="LLM-as-a-Judge Evaluator cho AI Project Manager")
    parser.add_argument("--input", type=str, required=True, help="Đường dẫn đến file JSON chứa dữ liệu (issue, ground_truth, ai_output)")
    parser.add_argument("--output", type=str, default="evaluation_report.json", help="Đường dẫn lưu report")
    args = parser.parse_args()

    input_file = args.input
    output_file = args.output

    print(f"Đọc dữ liệu từ {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    total = len(data)
    print(f"Đã load {total} cases. Bắt đầu chấm điểm bằng LLM Judge ({MODEL_NAME})...")
    
    results = []
    processed_ids = set()
    
    if os.path.exists(output_file):
        print(f"Found existing {output_file}, loading processed cases to resume...")
        with open(output_file, 'r', encoding='utf-8') as f:
            try:
                existing_report = json.load(f)
                if "details" in existing_report:
                    # Keep successful ones
                    results = [r for r in existing_report["details"] if r.get("status") == "success"]
                    processed_ids = {r.get("id") for r in results}
                    print(f"Resuming... Skipped {len(processed_ids)} already successfully evaluated items.")
            except json.JSONDecodeError:
                pass

    # Filter items that need processing
    items_to_process = [item for item in data if item.get("id", "") not in processed_ids]
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(evaluate_single_case, item, i, total) for i, item in enumerate(items_to_process)]
        for future in as_completed(futures):
            results.append(future.result())
            
            # Save incrementally after each completion
            temp_success = sum(1 for r in results if r["status"] == "success")
            temp_report = {
                "summary": {
                    "total_cases": total,
                    "success_cases": temp_success,
                    "average_scores": {}
                },
                "details": results
            }
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(temp_report, f, indent=2, ensure_ascii=False)
            
    # Tính điểm trung bình
    avg_scores = {k: 0.0 for k in results[0]["scores"].keys()} if results else {}
    success_count = sum(1 for r in results if r["status"] == "success")
    
    if success_count > 0:
        for r in results:
            if r["status"] == "success":
                for k, v in r["scores"].items():
                    avg_scores[k] += v
        for k in avg_scores:
            avg_scores[k] = round(avg_scores[k] / success_count, 2)
            
    report = {
        "summary": {
            "total_cases": total,
            "success_cases": success_count,
            "average_scores": avg_scores
        },
        "details": results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print(f"\nĐã hoàn tất! Báo cáo được lưu tại: {output_file}")
    print("Điểm trung bình (Average Scores):")
    print(json.dumps(avg_scores, indent=2))

if __name__ == "__main__":
    main()
