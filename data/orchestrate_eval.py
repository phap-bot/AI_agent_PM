import json
import os
import sys
import time
import re
from pathlib import Path
from collections import defaultdict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from ai_scrum_master.core.llm.setup import build_llm
from ai_scrum_master.core.llm.json_utils import normalize_llm_json_output
from dotenv import load_dotenv
from openai import OpenAI

env_path = Path(__file__).parent.parent / "src" / "ai_scrum_master" / ".env"
load_dotenv(dotenv_path=env_path)

DATA_FILE = Path(__file__).parent / "clean_requirements.json"
PM_OUTPUT_FILE = Path(__file__).parent / "generated_features_output.json"
GEMINI_OUTPUT_FILE = Path(__file__).parent / "gemini_ground_truth.json"

def calculate_classification_metrics(y_true, y_pred):
    classes = set(y_true) | set(y_pred)
    macro_p, macro_r, macro_f1 = 0.0, 0.0, 0.0
    
    for cls in classes:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp == cls)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != cls and yp == cls)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp != cls)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        macro_p += precision
        macro_r += recall
        macro_f1 += f1
        
    num_classes = len(classes) if classes else 1
    return {
        "macro_precision": macro_p / num_classes,
        "macro_recall": macro_r / num_classes,
        "macro_f1": macro_f1 / num_classes,
    }

def get_openrouter_client():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY"):
                    api_key = line.split("=", 1)[1].strip().split(",")[0]
                    break
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

def run():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    total_to_run = min(len(data), 20)
    samples = data[:total_to_run]
    
    print(f"🚀 Bắt đầu đánh giá trên {total_to_run} mẫu...")
    
    # BƯỚC 1: Dùng pm-agent để dự đoán
    print("\n--- BƯỚC 1: Dùng PM-Agent dự đoán 4 features ---")
    pm_llm = build_llm(temperature=0.0)
    pm_results = []
    
    system_prompt = """You are an expert Technical Product Manager.
Classify the following software requirement into exactly 4 categories:
1. "type": ["bug", "feature", "maintenance"]
2. "domain": ["ui/ux", "backend", "collaboration", "devops", "general"]
3. "complexity": ["low", "medium", "high"]
4. "team": ["be", "fe", "qa", "fullstack"]

Output ONLY a valid JSON object. Do NOT include markdown tags like ```json.
Example: {"type": "feature", "domain": "backend", "complexity": "medium", "team": "be"}"""

    for i, item in enumerate(samples):
        req = item["requirement"]
        print(f"PM-Agent [{i+1}/{total_to_run}]: {req[:50]}...")
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Requirement: {req}"}]
        
        try:
            resp = pm_llm.call(messages)
            json_text = normalize_llm_json_output(resp)
            json_text = re.sub(r"<think>.*?</think>", "", json_text, flags=re.DOTALL).strip()
            pred = json.loads(json_text)
            pm_results.append({"requirement": req, "pm_prediction": pred})
        except Exception as e:
            print(f"Lỗi PM-Agent: {e}")
            pm_results.append({"requirement": req, "pm_prediction": {}})
            
    with open(PM_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(pm_results, f, indent=2, ensure_ascii=False)

    # BƯỚC 2: Dùng OpenRouter (Gemini/GPT) làm Ground Truth
    print("\n--- BƯỚC 2: Dùng OpenRouter làm AI Ground Truth ---")
    client = get_openrouter_client()
    gemini_results = []
    
    for i, item in enumerate(samples):
        req = item["requirement"]
        print(f"OpenRouter [{i+1}/{total_to_run}]...")
        prompt = system_prompt + f"\n\nRequirement:\n{req}"
        
        retry_count = 0
        success = False
        while retry_count < 3 and not success:
            try:
                resp = client.chat.completions.create(
                    model="openai/gpt-oss-120b:free",
                    messages=[{"role": "user", "content": prompt}],
                    extra_body={"reasoning": {"enabled": True}}
                )
                text = resp.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                pred = json.loads(text)
                gemini_results.append({"requirement": req, "ai_ground_truth": pred})
                success = True
                time.sleep(10) # Chờ 10s sau mỗi request thành công
            except Exception as e:
                print(f"Lỗi OpenRouter (sẽ thử lại sau 15s): {e}")
                retry_count += 1
                time.sleep(15) # Chờ 15s trước khi retry
                
        if not success:
            gemini_results.append({"requirement": req, "ai_ground_truth": {}})
            
    with open(GEMINI_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(gemini_results, f, indent=2, ensure_ascii=False)

    # BƯỚC 3: So sánh và chấm điểm
    print("\n--- BƯỚC 3: Đánh giá Metrics (Accuracy, Precision, Recall, F1) ---")
    
    features = ["type", "domain", "complexity", "team"]
    y_true = {f: [] for f in features}
    y_pred = {f: [] for f in features}
    
    for pm_item, gemini_item in zip(pm_results, gemini_results):
        pm_pred = pm_item.get("pm_prediction", {})
        gt = gemini_item.get("ai_ground_truth", {})
        
        for f in features:
            y_pred[f].append(pm_pred.get(f, "unknown").lower())
            y_true[f].append(gt.get(f, "unknown").lower())
            
    report = f"======================================\n📊 BENCHMARK REPORT: PM-Agent vs OpenRouter\n======================================\nTổng số mẫu: {total_to_run}\n"
    
    for f in features:
        yt = y_true[f]
        yp = y_pred[f]
        acc = sum(1 for t, p in zip(yt, yp) if t == p) / total_to_run * 100
        metrics = calculate_classification_metrics(yt, yp)
        
        report += f"\n✅ {f.upper()}\n"
        report += f"   - Accuracy  : {acc:.2f}%\n"
        report += f"   - Precision : {metrics['macro_precision']*100:.2f}% (Macro Avg)\n"
        report += f"   - Recall    : {metrics['macro_recall']*100:.2f}% (Macro Avg)\n"
        report += f"   - F1-Score  : {metrics['macro_f1']*100:.2f}% (Macro Avg)\n"
        
    print(report)
    with open(Path(__file__).parent / "benchmark_report_final.txt", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    run()
