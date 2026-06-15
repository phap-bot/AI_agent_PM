# 🚀 AI Scrum Master Agent (Next-Gen Architecture)

AI Scrum Master Agent là một hệ thống tự động hoá thông minh, giúp chuyển đổi các yêu cầu thô (raw requirements) từ các bên liên quan (stakeholders) thành các Jira work items (sprint-ready) thông qua một quy trình hoàn chỉnh. 

Hệ thống đã được nâng cấp toàn diện sang kiến trúc Bất đồng bộ (Asynchronous) với Celery, lưu trữ vector bằng Qdrant và sử dụng các mô hình AI chuyên biệt (Qwen 2.5 Coder) được Fine-tune riêng cho tác vụ Product Management.

**Quy trình hoạt động (Multi-Agent Pipeline):**
`User Request ➔ FastAPI ➔ Redis Queue ➔ Celery Worker ➔ CrewAI (Researcher ➔ Planner ➔ Evaluator) ➔ Human Approval ➔ Jira/Slack Action`

---

## 🛠️ Tech Stack & Architecture

- **Agent Framework:** CrewAI (Researcher, Planner, Evaluator)
- **Backend API:** FastAPI
- **Frontend UI:** React (Vite)
- **Background Tasks:** Celery + Redis (Message Queue)
- **Database:** MongoDB (Lưu trữ lịch sử)
- **Vector Store:** Qdrant (Lưu trữ tài liệu dự án RAG)
- **LLM Runtime:** Ollama (Chạy 100% Local, bảo mật dữ liệu)
- **AI Models:**
  - `qwen2.5-coder:7b`: Tác vụ Research (Hỗ trợ Tool Calling, trích xuất tài liệu)
  - `pm_planner_7b`: Tác vụ Planning (Mô hình Qwen 2.5 Coder được Fine-tune chuyên biệt bằng Unsloth)
  - `qwen-embed`: Tác vụ Embedding nhúng dữ liệu tài liệu

---

## 🤖 1. Thiết lập Mô hình AI (Ollama)

Hệ thống yêu cầu 3 mô hình AI chạy local thông qua Ollama.

**1. Cài đặt các mô hình gốc:**
```bash
ollama pull qwen2.5-coder:7b
ollama pull qwen-embed
```

**2. Khởi tạo mô hình Planner đã được Fine-tune:**
Mô hình `pm_planner_7b` là linh hồn của hệ thống, được huấn luyện riêng biệt từ Data Vàng của PM. 
- Sau khi chạy file [Google Colab/Kaggle Fine-tune](project_colab.zip), bạn sẽ nhận được một file `.gguf`.
- Chép file `.gguf` đó vào thư mục `src/Models/`.
- Mở Terminal tại thư mục `src/Models/` và chạy lệnh sau để đưa mô hình vào Ollama:
```powershell
ollama create pm_planner_7b -f Modelfile.txt
```

---

## 🐳 2. Khởi chạy Hệ thống bằng Docker Compose

Hệ thống đã được Docker hóa hoàn toàn. Bạn không cần tự cài đặt DB hay Redis.

**1. Copy file cấu hình:**
Đảm bảo bạn đã sao chép `src/ai_scrum_master/.env.example` thành `src/ai_scrum_master/.env` và cấu hình các biến cơ bản.

**2. Chạy toàn bộ hệ thống:**
Mở Terminal tại thư mục gốc của project và gõ lệnh:
```bash
docker-compose up -d
```
Lệnh này sẽ tự động tải các base image và khởi động 6 Containers:
1. `api_local` (FastAPI chạy ở port 8000)
2. `ui_local` (React chạy ở port 5173)
3. `worker_local` (Celery Worker xử lý AI ngầm)
4. `mongodb_local` (Database cổng 27017)
5. `qdrant_local` (Vector DB cổng 6333)
6. `redis_local` (Message Broker cổng 6379)

**Truy cập ứng dụng:**
- **Giao diện người dùng:** [http://localhost:5173](http://localhost:5173)
- **Tài liệu API Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 💻 3. Quy trình Local Development (Code Nhàn Tênh)

Hệ thống đã được cấu hình **Hot-Reload thông qua Docker Volumes** và tối ưu hoá `.dockerignore`. 

- **KHÔNG CẦN CHẠY LẠI `--build`:** Trừ khi bạn sửa file `requirements.txt` hoặc `package.json`, bạn tuyệt đối không cần dùng lệnh `--build`.
- **Sửa API (Python) hoặc UI (React):** Hệ thống sử dụng `uvicorn --reload` và `vite`. Bạn chỉ cần gõ code, ấn Save (Ctrl+S), ứng dụng sẽ tự cập nhật ngay lập tức.
- **Sửa Worker (Celery Task):** Do đặc thù của Celery, mỗi khi sửa code liên quan đến agent hoặc pipeline trong Worker, bạn hãy nạp lại code mới bằng đúng một lệnh siêu tốc:
  ```bash
  docker-compose restart worker
  ```

---

## ⚙️ 4. Cấu hình Biến Môi Trường (.env)

Các biến quan trọng cần lưu ý trong file `src/ai_scrum_master/.env`:

```env
# Ollama LLM Config
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_REASONING_MODEL=pm_planner_7b
OLLAMA_RESEARCHER_MODEL=qwen2.5-coder:7b
OLLAMA_EMBED_MODEL=qwen-embed

# Database Config
MONGODB_URI=mongodb://mongodb:27017
QDRANT_URL=http://qdrant:6333
RAG_BACKEND=direct_qdrant

# Background Worker
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Integrations (Tuỳ chọn để test Action)
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_PROJECT_KEY=SCRUM
JIRA_API_TOKEN=xxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
```

---

## ⚠️ 5. Gỡ Lỗi Thường Gặp (Troubleshooting)

### ❌ Lỗi: `pm_planner_7b does not support tools`
- **Nguyên nhân:** Mô hình tự tạo thông qua `Modelfile` không hỗ trợ gọi hàm Python (Function Calling). Mà con `Researcher Agent` bắt buộc phải xài Tool để tìm tài liệu.
- **Giải pháp:** Kiểm tra lại file `.env` xem biến `OLLAMA_RESEARCHER_MODEL` đã được cấu hình đúng là `qwen2.5-coder:7b` chưa. Sau đó chạy lệnh `docker-compose restart worker`.

### ⏳ Hệ thống treo / Chạy rất lâu khi ấn Generate
- **Nguyên nhân:** Đây không phải lỗi. API đã đẩy lệnh xuống cho Worker xử lý ngầm (Asynchronous). Model LLM chạy local nên thời gian phân tích có thể tốn từ 2-5 phút tuỳ độ mạnh của Card đồ hoạ (VRAM).
- **Giải pháp:** Bạn có thể xem dòng suy nghĩ (Brainwaves) của hệ thống AI theo thời gian thực bằng cách xem log của Worker:
  ```bash
  docker-compose logs -f worker
  ```

### 💥 Lỗi bộ nhớ / Unable to allocate CPU buffer (OOM)
- **Nguyên nhân:** Máy không đủ RAM hoặc Card đồ họa thiếu VRAM.
- **Giải pháp:** 
  1. Đảm bảo bạn chỉ cài các model 4-bit (q4_k_m)
  2. Giảm giá trị `OLLAMA_NUM_CTX` trong file `.env` xuống (VD: `4096` hoặc `2048`).
