import json
import os
import sys
import time
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

env_path = Path(__file__).parent.parent / "src" / "ai_scrum_master" / ".env"
load_dotenv(dotenv_path=env_path)

DATA_FILE = "llm_evaluated_requirements.json"
REPORT_FILE = "benchmark_report_local.txt"

def calculate_classification_metrics(y_true, y_pred):
    classes = set(y_true) | set(y_pred)
    metrics_per_class = {}
    macro_p, macro_r, macro_f1 = 0.0, 0.0, 0.0
    
    for cls in classes:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp == cls)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != cls and yp == cls)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp != cls)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        metrics_per_class[cls] = {"precision": precision, "recall": recall, "f1": f1}
        macro_p += precision
        macro_r += recall
        macro_f1 += f1
        
    num_classes = len(classes) if classes else 1
    return {
        "macro_precision": macro_p / num_classes,
        "macro_recall": macro_r / num_classes,
        "macro_f1": macro_f1 / num_classes,
    }

def run():
    data_path = Path(__file__).parent / DATA_FILE
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print("🚀 Khởi tạo Model Local (pm-agent)...", flush=True)
    llm = build_llm(temperature=0.0)

    system_prompt = """
You are an expert Agile Scrum Master and Technical Product Manager.
Classify the following software requirement into exactly three categories:
1. "type": Must be one of ["bug", "feature", "maintenance"].
2. "domain": Must be one of ["ui/ux", "backend", "collaboration", "devops", "general"].
3. "complexity": Must be one of ["low", "medium", "high"].

Return ONLY a valid JSON object. Do NOT include markdown tags like ```json.
Example output:
{"type": "feature", "domain": "backend", "complexity": "medium"}
"""

    total_to_run = min(len(data), 20) # Test 20 mẫu
    print(f"Bắt đầu chạy Benchmark trên {total_to_run} mẫu...", flush=True)
    
    y_true_type, y_pred_type = [], []
    y_true_domain, y_pred_domain = [], []
    y_true_comp, y_pred_comp = [], []
    failed_cases = []
    
    for i, item in enumerate(data[:total_to_run]):
        requirement = item["requirement"]
        ground_truth = item["ai_ground_truth"]
        
        print(f"[{i+1:02d}/{total_to_run}] Đang xử lý...", flush=True)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Requirement: {requirement}"}
        ]
        
        try:
            response_raw = llm.call(messages)
            json_text = normalize_llm_json_output(response_raw)
            import re
            json_text = re.sub(r"<think>.*?</think>", "", json_text, flags=re.DOTALL).strip()
            predicted = json.loads(json_text)
            
            gt_type = ground_truth.get("type", "unknown")
            gt_domain = ground_truth.get("domain", "unknown")
            gt_comp = ground_truth.get("complexity", "unknown")
            
            p_type = predicted.get("type", "unknown")
            p_domain = predicted.get("domain", "unknown")
            p_comp = predicted.get("complexity", "unknown")
            
            y_true_type.append(gt_type)
            y_pred_type.append(p_type)
            y_true_domain.append(gt_domain)
            y_pred_domain.append(p_domain)
            y_true_comp.append(gt_comp)
            y_pred_comp.append(p_comp)
            
            if (p_type != gt_type) or (p_domain != gt_domain) or (p_comp != gt_comp):
                failed_cases.append({
                    "req_preview": requirement[:100] + "...",
                    "pred": predicted,
                    "truth": ground_truth
                })
        except Exception as e:
            print(f"Lỗi: {e}", flush=True)

    acc_type = sum(1 for yt, yp in zip(y_true_type, y_pred_type) if yt == yp) / total_to_run * 100
    acc_domain = sum(1 for yt, yp in zip(y_true_domain, y_pred_domain) if yt == yp) / total_to_run * 100
    acc_comp = sum(1 for yt, yp in zip(y_true_comp, y_pred_comp) if yt == yp) / total_to_run * 100

    metrics_type = calculate_classification_metrics(y_true_type, y_pred_type)
    metrics_domain = calculate_classification_metrics(y_true_domain, y_pred_domain)
    metrics_comp = calculate_classification_metrics(y_true_comp, y_pred_comp)
    
    report_content = f"""
======================================
📊 BENCHMARK REPORT (Model: pm-agent local)
======================================
Tổng số mẫu đánh giá: {total_to_run}

✅ TYPE (Bug/Feature/Maintenance)
   - Accuracy : {acc_type:.2f}%
   - F1-Score : {metrics_type['macro_f1']*100:.2f}% (Macro Avg)

✅ DOMAIN
   - Accuracy : {acc_domain:.2f}%
   - F1-Score : {metrics_domain['macro_f1']*100:.2f}% (Macro Avg)

✅ COMPLEXITY
   - Accuracy : {acc_comp:.2f}%
   - F1-Score : {metrics_comp['macro_f1']*100:.2f}% (Macro Avg)

--------------------------------------
🚨 CÁC TRƯỜNG HỢP DỰ ĐOÁN SAI:
"""
    for case in failed_cases[:5]:
        report_content += f"\n- Req: {case['req_preview']}\n  > Đoán: {case['pred']}\n  > Chuẩn: {case['truth']}\n"

    print(report_content)
    with open(Path(__file__).parent / REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_content)

if __name__ == "__main__":
    run()
