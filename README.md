# AI Scrum Master Agent

AI Scrum Master Agent là hệ thống đa tác tử chạy cục bộ, dùng để chuyển yêu cầu thô từ stakeholder thành các hạng mục công việc sẵn sàng đưa vào sprint. Dự án kết hợp FastAPI, Celery, LangGraph, Ollama, MongoDB, Redis, Qdrant và giao diện React/Vite để hỗ trợ quy trình vận hành sản phẩm.

## Chức Năng Chính

- Nhận yêu cầu thô từ giao diện web hoặc API.
- Truy xuất ngữ cảnh dự án từ thư viện tài liệu đã ingest.
- Điều phối yêu cầu qua pipeline nhiều tác tử:
  - `RouterAgent`
  - `ResearcherAgent`
  - `PlannerAgent`
  - `EvaluatorAgent`
- Sinh bản nháp story có cấu trúc, gồm:
  - user story
  - acceptance criteria
  - story points
  - task BE/FE/QA
  - definition of done
  - phản hồi từ evaluator
- Xem trước hoặc thực thi hành động downstream trên Jira, Slack và GitHub.

## Kiến Trúc

```text
Frontend (React/Vite)
        |
        v
FastAPI API
        |
        v
Celery + Redis
        |
        v
LangGraph Pipeline
  -> Router
  -> Researcher (RAG qua Qdrant)
  -> Planner (LLM)
  -> Evaluator (rules + LLM tùy chọn)
        |
        +--> MongoDB lưu lịch sử/job
        +--> Jira / Slack / GitHub actions
```

## Tech Stack

- Backend: FastAPI, Python 3.11
- Worker: Celery, Redis
- Điều phối LLM: LangGraph, LangChain
- Mô hình cục bộ: Ollama
- Vector store: Qdrant
- Lưu trữ: MongoDB
- Frontend: React 19, Vite, Tailwind CSS, i18next
- Triển khai local: Docker Compose
- Kiểm thử: pytest

## Cấu Trúc Thư Mục

```text
frontend/                         Giao diện React
src/ai_scrum_master/api/          API routes và schemas của FastAPI
src/ai_scrum_master/agents/       Router, Researcher, Planner, Evaluator
src/ai_scrum_master/core/         Config, pipeline, validation, tiện ích
src/ai_scrum_master/ingestion/    Parse, chunk và index tài liệu
src/ai_scrum_master/retrieval/    RAG và truy cập vector store
src/ai_scrum_master/worker/       Celery app và background tasks
tests/                            Unit test và integration-style test
```

## Luồng Xử Lý Chính

### 1. Sinh User Story

1. Frontend gửi `POST /generate`.
2. API tạo background job.
3. Celery chạy pipeline LangGraph.
4. UI polling trạng thái qua `/generate/status/{job_id}`.
5. Kết quả cuối cùng được lưu vào lịch sử trong MongoDB.

### 2. Ingest Tài Liệu

1. Frontend upload file `.pdf`, `.docx`, `.txt` hoặc `.md`.
2. Hệ thống parse và chia nhỏ nội dung thành chunks.
3. Chunks được embedding bằng mô hình embedding của Ollama.
4. Vectors được upsert vào Qdrant.
5. Retrieval có thể lọc theo phạm vi dự án qua `project_id`.

### 3. Sprint Và Actions

- Xem trước và tạo Jira story.
- Xem trước và gửi thông báo Slack.
- Tạo GitHub branch sau khi Jira thành công.
- Tải sprint board, chuyển trạng thái issue và hoàn tất sprint.

## Nguyên Tắc Bắt Buộc

- Không tạo Jira issue trước khi evaluation đạt yêu cầu.
- Nếu yêu cầu mơ hồ, tạo câu hỏi làm rõ trước khi lập kế hoạch story.
- Nếu phạm vi quá lớn cho một sprint, tách thành nhiều story và đề xuất phân bổ sprint.
- Nếu retrieval không có ngữ cảnh hữu ích, tiếp tục với cảnh báo và giả định rõ ràng.
- Vòng revision tối đa 3 lần trước khi escalation.
- Task breakdown phải tách theo BE / FE / QA.
- Story points chỉ dùng Fibonacci: `1`, `2`, `3`, `5`, `8`, `13`.

## Chuẩn Đầu Ra

- Mỗi story phải theo định dạng: `As a / I want / So that`.
- Mỗi story phải có ít nhất 3 acceptance criteria dạng `Given / When / Then`.
- Mỗi story phải có definition of done.
- Planner nên trả về dữ liệu machine-readable khi có thể.
- Evaluator chỉ trả về một trong hai trạng thái: `APPROVED` hoặc `REVISION`.

## Cấu Hình Môi Trường

Sao chép file env mẫu:

```bash
cp src/ai_scrum_master/.env.example src/ai_scrum_master/.env
```

Các biến quan trọng:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_REASONING_MODEL=Pm-agent
OLLAMA_RESEARCHER_MODEL=qwen2.5-coder:7b
OLLAMA_EMBED_MODEL=bge-m3

MONGODB_URI=mongodb://mongodb:27017
QDRANT_URL=http://qdrant:6333
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

Tích hợp tùy chọn:

```env
JIRA_BASE_URL=
JIRA_PROJECT_KEY=
JIRA_EMAIL=
JIRA_API_TOKEN=

SLACK_WEBHOOK_URL=

QDRANT_COLLECTION=ai_scrum_master_context
```

## Chạy Local

Khởi động toàn bộ stack bằng Docker Compose:

```bash
docker-compose up -d
```

Các service mặc định:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`
- MongoDB: `localhost:27017`
- Qdrant: `localhost:6333`
- Redis: `localhost:6379`

## Lệnh Hữu Ích

Chạy test backend:

```bash
pytest
```

Build frontend:

```bash
cd frontend
npm run build
```

Restart worker sau khi thay đổi pipeline:

```bash
docker-compose restart worker
```

## Ghi Chú Hiện Tại

- Hệ thống ưu tiên Ollama chạy cục bộ, không mặc định dùng hosted LLM API.
- Planner và evaluator kết hợp LLM với validation rule để giảm rủi ro tạo Jira output sai.
- Retrieval hỗ trợ ngữ cảnh theo dự án khi tài liệu được ingest với `project_id`.
- Tài liệu upload được index tăng dần.
- Với GPU VRAM thấp, nên dùng model quantized, context window vừa phải và cấu hình runtime thận trọng để tránh OOM.

## License

Dự án nội bộ, trừ khi team định nghĩa license khác.
