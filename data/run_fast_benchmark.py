import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ai_scrum_master.retrieval.vector_store import search_context
from src.ai_scrum_master.core.llm.setup import build_llm
from ai_scrum_master.core.llm.json_utils import normalize_llm_json_output

DATASET_FILE = r"d:\Antigravity\AI_Agent_PM_PRJ\data\vscode_closed_dataset.json"
OUTPUT_FILE = r"d:\Antigravity\AI_Agent_PM_PRJ\data\ai_planner_output.json"

SYSTEM_PROMPT = """You are an expert Technical Product Manager.
Your job is to analyze the user's issue (Title and Body) along with the provided source code context, and generate a User Story, Acceptance Criteria, and Tasks.

OUTPUT FORMAT REQUIREMENTS:
You MUST output ONLY a valid JSON object. Do not wrap it in markdown. Do not include any explanations outside of the JSON.
The JSON must strictly follow this structure:
{
  "title": "Short title of the story",
  "story_type": "software_feature", 
  "jira_issue_type": "Story",
  "jira_labels": ["backend", "frontend", "bug", etc],
  "jira_linked_items": [],
  "user_story": "As a [role], I want to [action] so that [benefit].",
  "acceptance_criteria": [
    "Given [precondition] When [action] Then [result]"
  ],
  "story_points": null, // Hoặc một số nguyên Fibonacci (1, 2, 3, 5, 8) đánh giá độ khó
  "tasks": {
    "be": ["Backend task 1", "Backend task 2"],
    "fe": ["Frontend task 1"],
    "qa": ["Test case 1"]
  },
  "definition_of_done": ["Code reviewed", "Tests passed"],
  "planning_status": "READY_FOR_SPRINT",
  "clarification_questions": [],
  "assumptions": [],
  "story_splits": [],
  "sprint_allocation": [],
  "context_sources": []
}

If the issue lacks so much context that it's impossible to deduce the required changes even with the provided code context, you may set "planning_status" to "NEEDS_CLARIFICATION" and provide your questions in "clarification_questions", leaving "tasks" empty. Otherwise, strive to generate concrete tasks.
"""

# Khởi tạo 1 LLM dùng chung cho tất cả các luồng để tránh init nhiều lần
# Lưu ý: Ollama tự xử lý concurrent requests bằng hàng đợi (queue/batching) ở phía server của nó.
llm = build_llm(temperature=0.0, timeout=1200, options={"keep_alive": "5m", "num_ctx": 8192})
file_lock = threading.Lock()

def process_issue(item, index, total):
    issue_id = item.get("id", "")
    title = item.get("input", {}).get("title", "")
    body = item.get("input", {}).get("body", "")
    
    print(f"[{index}/{total}] Researching context for {issue_id}...")
    try:
        # Bước 1: RAG bằng Python trực tiếp
        query = f"Title: {title}\nBody: {body}"
        matches = search_context(query=query, n_results=5)
        
        context_texts = []
        for match in matches:
            meta = match.get("metadata", {})
            file_name = meta.get("file_name", "Unknown File")
            doc = match.get("document", "")
            if not doc:
                 doc = match.get("page_content", "")
            context_texts.append(f"--- File: {file_name} ---\n{doc}")
            
        rag_context = "\n\n".join(context_texts) if context_texts else "No relevant context found."
        
        # Cắt bớt RAG context nếu nó quá dài để tránh lỗi vượt quá 8192 tokens của Ollama
        max_context_chars = 10000 # Khoảng ~3000 tokens an toàn
        if len(rag_context) > max_context_chars:
            rag_context = rag_context[:max_context_chars] + "\n... [TRUNCATED DUE TO CONTEXT LIMIT]"
        
        # Bước 2: Gọi LLM trực tiếp với Context đã nạp (Prompt Collapse)
        user_prompt = f"""
ISSUE TITLE: {title}
ISSUE BODY: {body}

--- RAG CONTEXT (SOURCE CODE) ---
{rag_context}
"""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        print(f"[{index}/{total}] Prompting LLM for {issue_id}...")
        resp = llm.call(messages)
        json_text = normalize_llm_json_output(resp)
        
        import re
        json_text = re.sub(r"<think>.*?</think>", "", json_text, flags=re.DOTALL).strip()
        
        planner_output = json.loads(json_text)
        
        result_data = {
            "id": issue_id,
            "ai_output": planner_output,
            "rag_context": rag_context
        }
        print(f"[{index}/{total}] ✅ Success for {issue_id}")
        return result_data
        
    except Exception as e:
        print(f"[{index}/{total}] ❌ Failed for {issue_id}: {e}")
        return {
            "id": issue_id,
            "ai_output": {},
            "rag_context": f"Error: {str(e)}"
        }

def save_results(results):
    with file_lock:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

def main():
    os.environ["ENABLE_LLM_LOGGING"] = "1"
    print(f"Reading dataset from {DATASET_FILE}")
    with open(DATASET_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    total = len(data)
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

    items_to_process = [(i+1, item) for i, item in enumerate(data) if item.get("id") not in processed_ids]
    print(f"Bắt đầu xử lý song song {len(items_to_process)} mẫu còn lại...")
    
    # Sử dụng ThreadPoolExecutor để chạy đồng thời (Async Pipelining)
    # 3 workers là an toàn để Ollama không bị nghẽn hay tràn VRAM
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for original_idx, item in items_to_process:
            futures.append(executor.submit(process_issue, item, original_idx, total))
            
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            # Lưu tệp sau khi mỗi issue hoàn thành
            save_results(results)
            
    print(f"\n🚀 Đã hoàn tất! Fast Pipeline output saved to {OUTPUT_FILE}")
    print("Bạn có thể chạy script merge_for_evaluation.py và llm_judge_evaluator.py ngay bây giờ!")

if __name__ == "__main__":
    main()
