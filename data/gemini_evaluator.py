import os
import sys
import json
import time

# Khắc phục lỗi in chữ tiếng Việt trên Windows Terminal
sys.stdout.reconfigure(encoding='utf-8')

try:
    from openai import OpenAI
except ImportError:
    print("Vui lòng cài đặt thư viện trước bằng lệnh: pip install openai")
    exit(1)

DATASET_FILE = r"d:\Antigravity\AI_Agent_PM_PRJ\data\clean_requirements.json"
OUTPUT_FILE = r"d:\Antigravity\AI_Agent_PM_PRJ\data\final_requirements_with_scores.json"
ENV_FILE = r"d:\Antigravity\AI_Agent_PM_PRJ\src\ai_scrum_master\.env"

# Cố gắng đọc API Key từ file .env
API_KEYS = []
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("OPENROUTER_API_KEY"):
                # Xóa bỏ khoảng trắng dư thừa
                val = line.split("=", 1)[1].strip()
                if "," in val:
                    API_KEYS.extend([k.strip() for k in val.split(",") if k.strip()])
                elif val:
                    API_KEYS.append(val)

if not API_KEYS:
    print(f"CẢNH BÁO: Không tìm thấy OPENROUTER_API_KEY trong file {ENV_FILE}.")
    print("Sẽ dùng API Key trực tiếp nếu có cấu hình trong mã nguồn, nếu không script sẽ báo lỗi.")
    # Dùng placeholder tránh crash nếu user set biến môi trường ngoài
    API_KEYS = [os.environ.get("OPENROUTER_API_KEY", "<YOUR_OPENROUTER_API_KEY>")]

current_key_index = 0

# Khởi tạo client OpenAI cho OpenRouter
def get_client(key):
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=key,
    )

client = get_client(API_KEYS[current_key_index])
MODEL_NAME = "openai/gpt-oss-120b:free"

PROMPT_TEMPLATE = """
You are an expert Technical Product Manager. Your task is to classify the following software development requirement.

Classify it into exactly these categories:
- type: "bug", "feature", or "maintenance"
- domain: "ui/ux", "backend", "collaboration", "devops", or "general"
- complexity: "high", "medium", or "low"

Output ONLY a valid JSON object with the keys: "type", "domain", "complexity". DO NOT wrap in markdown blocks.

Requirement:
{requirement_text}
"""

def evaluate_with_openai():
    with open(DATASET_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"Bắt đầu dùng OpenRouter ({MODEL_NAME}) để chấm điểm {len(data)} requirements...")
    
    metrics = {"type": {"match": 0, "total": 0}, 
               "domain": {"match": 0, "total": 0}, 
               "complexity": {"match": 0, "total": 0}}

    evaluated_data = []
    requests_count = 0

    for i, item in enumerate(data):
        req_text = item.get("requirement", "")
        
        # Nhãn do script Heuristic (từ khóa) trước đó tự đoán
        heuristic_type = item.get("type", "")
        heuristic_domain = item.get("domain", "")
        heuristic_complexity = item.get("complexity", "")
        
        prompt = PROMPT_TEMPLATE.format(requirement_text=req_text)
        
        global current_key_index
        global client
        
        retry_count = 0
        success = False
        
        while retry_count <= len(API_KEYS):
            try:
                # Đổi key nếu đã gọi 15 lần (nếu dùng free tier OpenRouter, có rate limit)
                if requests_count >= 15 and len(API_KEYS) > 1:
                    current_key_index = (current_key_index + 1) % len(API_KEYS)
                    client = get_client(API_KEYS[current_key_index])
                    requests_count = 0
                    print(f"--- Đã chạy 15 request. Tự động đổi sang API KEY thứ {current_key_index + 1} ---")
                
                # Gọi OpenAI / OpenRouter API
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    # OpenRouter support cho "reasoning" (chỉ một số model support)
                    extra_body={"reasoning": {"enabled": True}}
                )
                
                requests_count += 1
                response_text = response.choices[0].message.content
                
                # Làm sạch response nếu model lỡ in thêm backticks markdown
                response_text = response_text.replace("```json", "").replace("```", "").strip()
                
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError:
                    print(f"[{i+1}/{len(data)}] Không parse được JSON: {response_text[:50]}...")
                    raise ValueError("Output is not valid JSON")
                
                ai_type = result.get("type", "").lower()
                ai_domain = result.get("domain", "").lower()
                ai_complexity = result.get("complexity", "").lower()
                
                # Chấm điểm độ đồng thuận (Agreement Rate)
                metrics["type"]["total"] += 1
                if ai_type == heuristic_type: metrics["type"]["match"] += 1
                    
                metrics["domain"]["total"] += 1
                if ai_domain == heuristic_domain: metrics["domain"]["match"] += 1
                    
                metrics["complexity"]["total"] += 1
                if ai_complexity == heuristic_complexity: metrics["complexity"]["match"] += 1

                evaluated_data.append({
                    "requirement": req_text[:200] + "...", # Rút gọn khi lưu file để dễ nhìn
                    "heuristic_guess": {
                        "type": heuristic_type,
                        "domain": heuristic_domain,
                        "complexity": heuristic_complexity
                    },
                    "ai_ground_truth": {
                        "type": ai_type,
                        "domain": ai_domain,
                        "complexity": ai_complexity
                    }
                })
                
                print(f"[{i+1}/{len(data)}] Xong. Trùng khớp -> Type: {ai_type==heuristic_type} | Domain: {ai_domain==heuristic_domain} | Comp: {ai_complexity==heuristic_complexity}")
                success = True
                
                # Rút ngắn thời gian sleep để check nhanh hơn
                time.sleep(2)
                break # Thành công thì thoát vòng lặp retry
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RateLimitError" in error_msg:
                    if len(API_KEYS) > 1:
                        print(f"[{i+1}/{len(data)}] Bị quá tải Rate Limit (429). Đổi API Key...")
                        current_key_index = (current_key_index + 1) % len(API_KEYS)
                        client = get_client(API_KEYS[current_key_index])
                        requests_count = 0
                        retry_count += 1
                        time.sleep(10)
                    else:
                        print(f"[{i+1}/{len(data)}] Bị giới hạn Rate Limit nhưng chỉ có 1 Key. Chờ 15 giây...")
                        time.sleep(15)
                        retry_count += 1
                else:
                    print(f"[{i+1}/{len(data)}] Lỗi khi gọi API: {e}")
                    break # Lỗi khác (không phải 429) thì bỏ qua requirement này

        if not success:
            print(f"[{i+1}/{len(data)}] Bỏ qua do gọi API thất bại quá nhiều lần.")

    # Ghi lại kết quả chi tiết
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(evaluated_data, f, indent=2, ensure_ascii=False)

    print("\n" + "="*50)
    print(f"KẾT QUẢ BENCHMARK (Heuristic vs {MODEL_NAME})")
    print("="*50)
    for field, counts in metrics.items():
        if counts["total"] > 0:
            agreement = (counts["match"] / counts["total"]) * 100
            print(f"Độ chính xác ({field.capitalize()}): {agreement:.2f}% ({counts['match']}/{counts['total']})")

    print(f"\nChi tiết kết quả đánh giá của AI đã được lưu tại:\n{OUTPUT_FILE}")

if __name__ == "__main__":
    evaluate_with_openai()
