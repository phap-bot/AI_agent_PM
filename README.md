# 🚀 AI Scrum Master Agent

AI Scrum Master Agent là một hệ thống tự động hoá thông minh, giúp chuyển đổi các yêu cầu thô (raw requirements) từ các bên liên quan (stakeholders) thành các Jira work items (sprint-ready) thông qua một quy trình hoàn chỉnh.

**Quy trình hoạt động (Pipeline):**
`Input ➔ Researcher ➔ Planner ➔ Evaluator ➔ Human Approval ➔ Jira/Slack Action Preview`

---

## 🛠️ Tech Stack

Hệ thống được xây dựng trên các công nghệ hiện đại và mạnh mẽ:

- **Agent Framework:** CrewAI
- **Backend API:** FastAPI
- **Frontend:** React (Vite)
- **LLM Runtime:** Ollama (chạy local tại `http://localhost:11434`)
- **Reasoning Model:** `deepseek-r1:7b`
- **Embedding Model:** `nomic-embed-text`
- **Vector Store:** ChromaDB (local persistent)
- **Testing:** pytest

> 💡 **Lưu ý:** Chức năng Jira/Slack hiện đang hoạt động ở chế độ **preview mode**. Ứng dụng chỉ tạo ra các payload/action plan để bạn xem trước, chưa thực hiện gọi API thực tế để tạo Jira issue hay gửi tin nhắn Slack.

---

## 📚 Kiến trúc & Tài liệu chi tiết
- **RAG System:** Tham khảo [RAG_DOCUMENTATION.md](docs/RAG_DOCUMENTATION.md) để hiểu cách hệ thống nhúng (embedding), tìm kiếm (hybrid search), và trích xuất ngữ cảnh dự án.
- **Agent Pipeline:** System prompt và role của các Agents được quản lý qua CrewAI.

---

## ⚙️ 1. Chuẩn bị môi trường

Đảm bảo bạn đang mở terminal ở thư mục gốc của dự án `D:/Antigravity/AI_Agent_PM_PRJ`.


**Sử dụng PowerShell (Windows):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## 🤖 2. Thiết lập & Chạy Ollama

Hệ thống sử dụng các mô hình ngôn ngữ lớn (LLM) chạy local thông qua Ollama để đảm bảo tính bảo mật và tiết kiệm chi phí.

1. **Cài đặt [Ollama](https://ollama.com/)** và khởi động server local.
2. **Tải các models bắt buộc:**
   ```bash
   ollama pull deepseek-r1:7b
   ollama pull nomic-embed-text
   ollama list
   ```
3. **Kiểm tra trạng thái Ollama đang hoạt động:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

**Tối ưu cấu hình (Khuyên dùng cho thiết bị có GPU VRAM hạn chế như RTX 3050 4GB):**
Để tránh lỗi Out of Memory, hãy cấu hình giới hạn qua các biến môi trường:
```bash
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_REASONING_MODEL=deepseek-r1:7b
export OLLAMA_EMBED_MODEL=nomic-embed-text
export OLLAMA_NUM_CTX=2048
export OLLAMA_TIMEOUT=180
export OLLAMA_TEMPERATURE=0.1
```

**Kiểm tra kết nối LLM thật bằng CrewAI + Ollama:**
```bash
python test_crewai_ollama.py
```
*(Lần đầu chạy có thể mất một chút thời gian để tải model vào bộ nhớ)*

---

## 🧠 3. Ingest Tài Liệu Vào ChromaDB (RAG Context)

Để Agent có đầy đủ thông tin bối cảnh (context) về dự án của bạn khi lập kế hoạch, bạn cần cung cấp các tài liệu (định dạng `.md` hoặc `.txt`).

1. Đặt các tài liệu vào thư mục:
   ```text
   src/ai_scrum_master/data/raw_docs/
   ```
2. Chạy quá trình ingest (đọc và lưu trữ thành dạng vector):
   ```bash
   PYTHONPATH=src python -m ai_scrum_master.ingestion.ingest
   ```

**Kết quả mong đợi:**
Bạn sẽ thấy báo cáo số lượng file được đọc: `{'collection': 'project_context', 'source_dir': '...', 'files_indexed': 1, ...}`. Dữ liệu ChromaDB sẽ được lưu trữ lâu dài tại `src/ai_scrum_master/data/chromadb/`.

---

## 🧪 4. Chạy Unit Tests

Hệ thống đi kèm với một bộ test nội bộ giúp bạn kiểm tra: chức năng Planner, Evaluator, tính hợp lệ của JSON schemas, và Action Preview.

```bash
python -m pytest tests/ -v
```

---

## 🚀 5. Chạy API Demo (FastAPI)

Khởi động backend server:
```bash
PYTHONPATH=src uvicorn ai_scrum_master.api.main:app --reload --host 127.0.0.1 --port 8000
```

**Kiểm tra API có hoạt động không:**
```bash
curl http://127.0.0.1:8000/health
# Trả về: {"status":"ok"}
```

**Gọi trực tiếp API pipeline để tạo User Story:**
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "requirement":"Add Google login for users using the existing JWT auth stack",
    "n_results":5
  }'
```

---

## 🎨 6. Chạy Giao Diện Frontend (React)

Hệ thống sử dụng React (Vite) cho giao diện người dùng. Để chạy Frontend:

1. Di chuyển vào thư mục `frontend`:
   ```bash
   cd frontend
   ```
2. Cài đặt các thư viện (chỉ cần chạy lần đầu):
   ```bash
   npm install
   ```
3. Khởi động môi trường phát triển (Dev Server):
   ```bash
   npm run dev
   ```

Giao diện sẽ được mở trên trình duyệt (thông thường là `http://localhost:5173`). Tại đây, bạn có thể nhập các yêu cầu tính năng và quan sát quá trình Agent phân tích và tạo Jira Stories.

---

## 🐳 7. Triển khai Production (Docker)

Hệ thống cung cấp sẵn `Dockerfile` và `docker-compose.yml` để bạn có thể chạy một cách độc lập và đồng nhất trên mọi môi trường.

1. **Khởi chạy bằng Docker Compose:**
   ```bash
   docker-compose up --build -d
   ```
   Lệnh này sẽ build image cho backend FastAPI và khởi chạy Frontend. Cả hai sẽ chạy nền.
   
2. **Kiểm tra Logs:**
   ```bash
   docker-compose logs -f
   ```
   
3. **Truy cập ứng dụng:**
   - Frontend UI: `http://localhost:5173`
   - Backend API: `http://localhost:8000`

> **Lưu ý Docker:** Ollama cần được cài đặt trên máy host. File `docker-compose.yml` đã được cấu hình trỏ tới `host.docker.internal:11434` để Backend container có thể gọi được Ollama trên máy của bạn.

---

## 🔗 8. Xem Trước Jira/Slack Action

Hệ thống chỉ khởi tạo thông tin gửi đến Jira/Slack khi tính năng đã được Evaluator phê duyệt (Status = `APPROVED`).

### Chuẩn bị Biến môi trường
Cần chuẩn bị những thông tin sau:
- **JIRA_BASE_URL**: URL site Atlassian của công ty (vd: `https://your-company.atlassian.net`)
- **JIRA_PROJECT_KEY**: Key của project (vd: `SCRUM`)
- **JIRA_EMAIL**: Email Atlassian của bạn
- **JIRA_API_TOKEN**: [Tạo API Token của Atlassian](https://id.atlassian.com/manage-profile/security/api-tokens)
- **SLACK_WEBHOOK_URL**: Lấy từ cài đặt Incoming Webhooks trong App Slack của bạn.

### Khởi tạo trên bash
```bash
export JIRA_BASE_URL=https://your-company.atlassian.net
export JIRA_PROJECT_KEY=SCRUM
export JIRA_EMAIL=your-email@company.com
export JIRA_API_TOKEN=your-atlassian-api-token
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
```

### Chạy API xem trước Jira Payload:
```bash
curl -X POST http://127.0.0.1:8000/actions/jira/preview \
  -H "Content-Type: application/json" \
  -d '{
    "story": {
      "title": "Google Login",
      "user_story": "As a user, I want Google login so that I can sign in faster.",
      "acceptance_criteria": ["Given Google auth is enabled..."],
      "story_points": 3,
      "tasks": {"be": ["OAuth callback"], "fe": ["Login button"], "qa": ["Auth tests"]},
      "definition_of_done": ["Acceptance criteria pass."]
    },
    "evaluation": {"status": "APPROVED", "issues": [], "revision_instructions": []}
  }'
```

---

## ⚠️ 9. Gỡ Lỗi Thường Gặp (Troubleshooting)

### ❌ `ModuleNotFoundError: No module named 'ai_scrum_master'`
Giải pháp là đảm bảo bạn đang đứng ở thư mục gốc của project hoặc set lại `PYTHONPATH`:
```bash
export PYTHONPATH=D:/Antigravity/AI_Agent_PM_PRJ
```

### ⏳ Ollama gọi quá lâu hoặc Timeout
Model có thể đang trong trạng thái "lạnh" chưa load vào RAM/VRAM. Hãy gọi nháp một câu trước khi chạy Pipeline:
```bash
ollama run deepseek-r1:7b "Return only: ok"
```

### 💥 Lỗi bộ nhớ / Unable to allocate CPU buffer (OOM)
Nếu card đồ họa của bạn không đủ đáp ứng, ứng dụng sẽ báo lỗi (thường hiện qua `OpenAI API call failed` do API tương thích ngược của CrewAI bị huỷ). Cách xử lý:
1. Chuyển xuống dùng model nhẹ hơn như `deepseek-r1:1.5b`.
2. Chỉnh `OLLAMA_NUM_CTX` xuống `1024` hoặc `512`.
```bash
ollama pull deepseek-r1:1.5b
export OLLAMA_REASONING_MODEL=deepseek-r1:1.5b
export OLLAMA_NUM_CTX=1024
```

### 🔍 ChromaDB báo `No relevant project context found`
Hiện tượng này nghĩa là chưa có tài liệu nào trong ChromaDB. Bạn hãy chạy lại câu lệnh Ingest ở phần **3. Ingest Tài Liệu Vào ChromaDB** phía trên.
