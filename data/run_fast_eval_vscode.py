import json
import os
import sys
import re
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.ai_scrum_master.core.llm.setup import build_llm
from ai_scrum_master.core.llm.json_utils import normalize_llm_json_output
from openai import OpenAI
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / "src" / "ai_scrum_master" / ".env"
load_dotenv(dotenv_path=env_path)

def get_openrouter_client():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY"):
                    api_key = line.split("=", 1)[1].strip().split(",")[0]
                    break
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

DATA_FILE = r"d:\Antigravity\AI_Agent_PM_PRJ\data\vscode_closed_dataset.json"
PM_OUTPUT_FILE = r"d:\Antigravity\AI_Agent_PM_PRJ\data\vscode_pm_prediction.json"
GEMINI_OUTPUT_FILE = r"d:\Antigravity\AI_Agent_PM_PRJ\data\vscode_gt_prediction.json"

SYSTEM_PROMPT = """You are an expert Technical Product Manager.
Classify the following software requirement into exactly 4 categories:
1. "type": ["bug", "feature", "maintenance"]
2. "domain": ["ui/ux", "backend", "collaboration", "devops", "general"]
3. "complexity": ["low", "medium", "high"]
4. "team": ["be", "fe", "qa", "fullstack"]

Output ONLY a valid JSON object. Do NOT include markdown tags like ```json.
Example: {"type": "feature", "domain": "backend", "complexity": "medium", "team": "be"}"""

# Global locks for thread-safe saving
pm_lock = threading.Lock()
gt_lock = threading.Lock()

# PM Agent processing
def process_pm(item, pm_llm, processed_ids):
    req_id = item.get("id", "")
    if req_id in processed_ids:
        return None
        
    title = item.get("input", {}).get("title", "")
    body = item.get("input", {}).get("body", "")
    req = f"Title: {title}\nBody: {body}"
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": f"Requirement: {req}"}]
    
    try:
        resp = pm_llm.call(messages)
        json_text = normalize_llm_json_output(resp)
        json_text = re.sub(r"<think>.*?</think>", "", json_text, flags=re.DOTALL).strip()
        pred = json.loads(json_text)
        return {"id": req_id, "requirement": req, "pm_prediction": pred}
    except Exception as e:
        print(f"[PM-Agent] Lỗi tại {req_id}: {e}")
        return {"id": req_id, "requirement": req, "pm_prediction": {}}

# OpenRouter Ground Truth processing
def process_gt(item, or_client, processed_ids):
    req_id = item.get("id", "")
    if req_id in processed_ids:
        return None
        
    title = item.get("input", {}).get("title", "")
    body = item.get("input", {}).get("body", "")
    req = f"Title: {title}\nBody: {body}"
    prompt = SYSTEM_PROMPT + f"\n\nRequirement:\n{req}"
    
    retry = 0
    while retry < 4:
        try:
            resp = or_client.chat.completions.create(
                model="openai/gpt-oss-120b:free",
                messages=[{"role": "user", "content": prompt}],
                extra_body={"reasoning": {"enabled": True}}
            )
            text = resp.choices[0].message.content.replace("```json", "").replace("```", "").strip()
            # Xóa các tag suy luận nếu có
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            pred = json.loads(text)
            return {"id": req_id, "requirement": req, "ai_ground_truth": pred}
        except Exception as e:
            retry += 1
            print(f"[OpenRouter] Lỗi tại {req_id} (thử lại {retry}/4): {e}")
            time.sleep(10 * retry) # Exponential backoff
            
    return {"id": req_id, "requirement": req, "ai_ground_truth": {}}

def calculate_classification_metrics(y_true, y_pred):
    classes = set(y_true)
    metrics = {"macro_precision": 0, "macro_recall": 0, "macro_f1": 0}
    for c in classes:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == c and p == c)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != c and p == c)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == c and p != c)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        metrics["macro_precision"] += precision
        metrics["macro_recall"] += recall
        metrics["macro_f1"] += f1
    n = len(classes) if classes else 1
    metrics = {k: v/n for k, v in metrics.items()}
    return metrics

def run():
    print("🚀 Bắt đầu đánh giá Fast Benchmark 2 (Label Classification)...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    pm_results = []
    pm_processed_ids = set()
    if os.path.exists(PM_OUTPUT_FILE):
        with open(PM_OUTPUT_FILE, "r", encoding="utf-8") as f:
            pm_results = json.load(f)
            pm_processed_ids = {r.get("id") for r in pm_results if r.get("id")}
            
    gt_results = []
    gt_processed_ids = set()
    if os.path.exists(GEMINI_OUTPUT_FILE):
        with open(GEMINI_OUTPUT_FILE, "r", encoding="utf-8") as f:
            gt_results = json.load(f)
            gt_processed_ids = {r.get("id") for r in gt_results if r.get("id")}

    print(f"--- BƯỚC 1: PM-Agent (Async Queue 3 workers) ---")
    pm_llm = build_llm(temperature=0.0)
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_pm, item, pm_llm, pm_processed_ids) for item in data]
        for future in as_completed(futures):
            res = future.result()
            if res:
                with pm_lock:
                    pm_results.append(res)
                    with open(PM_OUTPUT_FILE, "w", encoding="utf-8") as f:
                        json.dump(pm_results, f, indent=2, ensure_ascii=False)
                print(f"✅ [PM-Agent] Xong {res['id']}")

    print(f"\n--- BƯỚC 2: OpenRouter AI Ground Truth (Async Queue 5 workers) ---")
    or_client = get_openrouter_client()
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_gt, item, or_client, gt_processed_ids) for item in data]
        for future in as_completed(futures):
            res = future.result()
            if res:
                with gt_lock:
                    gt_results.append(res)
                    with open(GEMINI_OUTPUT_FILE, "w", encoding="utf-8") as f:
                        json.dump(gt_results, f, indent=2, ensure_ascii=False)
                print(f"✅ [OpenRouter] Xong {res['id']}")

    print("\n--- BƯỚC 3: Đánh giá Metrics (Accuracy, Precision, Recall, F1) ---")
    features = ["type", "domain", "complexity", "team"]
    y_true = {f: [] for f in features}
    y_pred = {f: [] for f in features}
    
    # Sort to align
    pm_results.sort(key=lambda x: x.get("id", ""))
    gt_results.sort(key=lambda x: x.get("id", ""))
    
    total_valid = 0
    for pm_item, gt_item in zip(pm_results, gt_results):
        if pm_item.get("id") != gt_item.get("id"):
            continue
        total_valid += 1
        pm_pred = pm_item.get("pm_prediction", {})
        gt = gt_item.get("ai_ground_truth", {})
        
        for f in features:
            y_pred[f].append(pm_pred.get(f, "unknown").lower())
            y_true[f].append(gt.get(f, "unknown").lower())
            
    report = f"======================================\n📊 BENCHMARK REPORT: PM-Agent vs OpenRouter\n======================================\nTổng số mẫu hợp lệ: {total_valid}\n"
    
    for f in features:
        yt = y_true[f]
        yp = y_pred[f]
        acc = sum(1 for t, p in zip(yt, yp) if t == p) / total_valid * 100 if total_valid > 0 else 0
        metrics = calculate_classification_metrics(yt, yp)
        
        report += f"\n✅ {f.upper()}\n"
        report += f"   - Accuracy  : {acc:.2f}%\n"
        report += f"   - Precision : {metrics['macro_precision']*100:.2f}% (Macro Avg)\n"
        report += f"   - Recall    : {metrics['macro_recall']*100:.2f}% (Macro Avg)\n"
        report += f"   - F1-Score  : {metrics['macro_f1']*100:.2f}% (Macro Avg)\n"
        
    print(report)
    with open(Path(__file__).parent / "benchmark_report_vscode_fast.txt", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    run()
