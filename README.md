# AI Scrum Master Agent

AI Scrum Master Agent chuyển yêu cầu thô của stakeholder thành Jira work item sprint-ready qua pipeline:

```text
Input -> Researcher -> Planner -> Evaluator -> Human Approval -> Jira/Slack Action Preview
```

Stack hiện tại:

- Agent framework: CrewAI
- API: FastAPI
- Demo UI: Streamlit
- LLM runtime: Ollama local tại `http://localhost:11434`
- Reasoning model: `deepseek-r1:7b`
- Embedding model: `nomic-embed-text`
- Vector store: ChromaDB local persistent
- Test: pytest

> Lưu ý: Jira/Slack hiện đang ở **preview mode**. App chỉ build payload/action plan, chưa gọi API thật để tạo Jira issue hoặc gửi Slack message.

## 1. Chuẩn bị môi trường

Chạy trong thư mục gốc dự án:

```bash
cd D:/Antigravity/AI_Agent_PM_PRJ
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn streamlit pytest crewai chromadb pyyaml pydantic
```

Nếu dùng PowerShell thay vì bash:

```powershell
cd D:\Antigravity\AI_Agent_PM_PRJ
.\.venv\Scripts\Activate.ps1
```

## 2. Chạy Ollama thật

Cài Ollama và chạy server local. Sau đó pull 2 model bắt buộc:

```bash
ollama pull deepseek-r1:7b
ollama pull nomic-embed-text
ollama list
```

Kiểm tra Ollama đang hoạt động:

```bash
curl http://localhost:11434/api/tags
```

Với RTX 3050 4GB VRAM, nên dùng context nhỏ để tránh OOM:

```bash
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_REASONING_MODEL=deepseek-r1:7b
export OLLAMA_EMBED_MODEL=nomic-embed-text
export OLLAMA_NUM_CTX=2048
export OLLAMA_TIMEOUT=180
export OLLAMA_TEMPERATURE=0.1
```

## 3. Kiểm tra LLM thật bằng CrewAI + Ollama

```bash
python test_crewai_ollama.py
```

Nếu thành công, terminal sẽ in response từ model Ollama local. Lần đầu chạy có thể chậm vì model cần warm up.

## 4. Ingest tài liệu thật vào ChromaDB

Đặt tài liệu dự án dạng `.md` hoặc `.txt` vào:

```text
src/ai_scrum_master/data/raw_docs/
```

Repo đã có sẵn context test để demo RAG thật:

```text
src/ai_scrum_master/data/raw_docs/auth_context.md
src/ai_scrum_master/data/raw_docs/checkout_context.md
src/ai_scrum_master/data/raw_docs/notification_context.md
src/ai_scrum_master/data/raw_docs/sprint_policy.md
```

Các request nên dùng để test trên giao diện/API thật:

```text
Add Google login for users using the existing JWT auth stack
Improve checkout retry behavior when payment provider times out
Notify the product delivery channel when a story is approved
Split a large marketplace launch request into sprint-ready work
```

Chạy ingestion thật, dùng embedding model `nomic-embed-text` qua Ollama:

```bash
PYTHONPATH=src python -m ai_scrum_master.ingestion.ingest
```

Kết quả mong đợi:

```text
{'collection': 'project_context', 'source_dir': '...', 'files_indexed': 1, 'chunks_indexed': 1}
```

Dữ liệu ChromaDB sẽ được lưu persistent tại:

```text
src/ai_scrum_master/data/chromadb/
```

## 5. Chạy test thật

Chạy toàn bộ pytest:

```bash
python -m pytest
```


```

Các test hiện tại chủ yếu kiểm tra:

- Planner tạo story đúng shape, có BE/FE/QA, story point Fibonacci.
- Evaluator trả `APPROVED` hoặc `REVISION` đúng rule.
- API function trả response đúng schema.
- Jira/Slack tool build preview payload đúng.
- Ingestion chunk text đúng.
- Runtime config YAML hợp lệ.

## 6. Chạy API demo thật

Start FastAPI:

```bash
PYTHONPATH=src uvicorn ai_scrum_master.api.main:app --reload --host 127.0.0.1 --port 8000
```

Mở health check:

```bash
curl http://127.0.0.1:8000/health
```

Kết quả mong đợi:

```json
{"status":"ok"}
```

Ingest qua API:

```bash
curl -X POST http://127.0.0.1:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"raw_docs_dir":"src/ai_scrum_master/data/raw_docs","collection_name":"project_context"}'
```

Generate story qua pipeline thật `Researcher -> Planner -> Evaluator -> Action Preview`:

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "requirement":"Add Google login for users using the existing JWT auth stack",
    "n_results":5
  }'
```

Response cần kiểm tra các phần chính:

- `context.documents`: context lấy từ ChromaDB.
- `story.user_story`: đúng format `As a / I want / so that`.
- `story.acceptance_criteria`: tối thiểu 3 dòng `Given / When / Then`.
- `story.story_points`: một trong `1, 2, 3, 5, 8, 13`.
- `story.tasks`: có đủ `be`, `fe`, `qa`.
- `evaluation.status`: `APPROVED` hoặc `REVISION`.
- `actions.jira` và `actions.slack`: preview payload, không execute thật.

## 7. Chạy Streamlit demo thật

Start UI:

```bash
streamlit run ui/app.py
```

Streamlit sẽ mở browser local. Hiện UI là placeholder để demo màn hình intake/review, chưa gọi API `/generate` trực tiếp. Để test pipeline thật trong lúc UI chưa nối API, chạy FastAPI ở bước 6 rồi gọi `/generate` bằng curl/Postman với các request mẫu ở bước 4.

Luồng demo thật khuyến nghị:

1. Start Ollama.
2. Ingest `src/ai_scrum_master/data/raw_docs`.
3. Start FastAPI.
4. Start Streamlit để mở màn hình demo.
5. Gọi `/generate` bằng curl/Postman và đối chiếu response với context mẫu.
6. Nếu response có `evaluation.status=APPROVED`, test Jira/Slack preview ở bước 8.

## 8. Preview Jira/Slack action

Jira/Slack action chỉ sẵn sàng khi evaluator trả `APPROVED`.

### Lấy Jira key và link

Bạn cần 4 giá trị:

| Biến môi trường | Lấy ở đâu | Ví dụ |
|---|---|---|
| `JIRA_BASE_URL` | URL site Atlassian của bạn, phần trước `/jira` hoặc `/browse` | `https://your-company.atlassian.net` |
| `JIRA_PROJECT_KEY` | Jira project → Project settings → Details → Key | `SCRUM` |
| `JIRA_EMAIL` | Email tài khoản Atlassian của bạn | `pm@company.com` |
| `JIRA_API_TOKEN` | Atlassian account → Security → API tokens → Create API token | `ATATT...` |

Cách lấy `JIRA_BASE_URL` và `JIRA_PROJECT_KEY` nhanh:

1. Mở Jira project trên browser.
2. Vào một issue bất kỳ, URL thường có dạng:

```text
https://your-company.atlassian.net/browse/SCRUM-123
```

3. Khi đó:

```text
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_PROJECT_KEY=SCRUM
```

Cách tạo `JIRA_API_TOKEN`:

1. Mở Atlassian account security page.
2. Vào mục API tokens.
3. Chọn Create API token.
4. Copy token ngay lúc tạo và lưu vào `.env` hoặc export env.

Không commit token thật vào git.

### Lấy Slack webhook link

Bạn cần 1 giá trị:

| Biến môi trường | Lấy ở đâu | Ví dụ |
|---|---|---|
| `SLACK_WEBHOOK_URL` | Slack app → Incoming Webhooks → Webhook URL | `https://hooks.slack.com/services/...` |

Cách tạo Slack Incoming Webhook:

1. Vào Slack API Apps.
2. Chọn Create New App.
3. Chọn From scratch.
4. Chọn workspace.
5. Vào Incoming Webhooks.
6. Bật Activate Incoming Webhooks.
7. Chọn Add New Webhook to Workspace.
8. Chọn channel nhận thông báo.
9. Copy Webhook URL.

Không public webhook URL vì ai có URL này đều có thể gửi message vào channel.

### Set biến môi trường

Set biến môi trường để preview payload ở trạng thái `ready=true`:

```bash
export JIRA_BASE_URL=https://your-company.atlassian.net
export JIRA_PROJECT_KEY=SCRUM
export JIRA_EMAIL=your-email@company.com
export JIRA_API_TOKEN=your-atlassian-api-token
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
```

PowerShell:

```powershell
$env:JIRA_BASE_URL="https://your-company.atlassian.net"
$env:JIRA_PROJECT_KEY="SCRUM"
$env:JIRA_EMAIL="your-email@company.com"
$env:JIRA_API_TOKEN="your-atlassian-api-token"
$env:SLACK_WEBHOOK_URL="https://hooks.slack.com/services/xxx/yyy/zzz"
```

Preview Jira payload:

```bash
curl -X POST http://127.0.0.1:8000/actions/jira/preview \
  -H "Content-Type: application/json" \
  -d '{
    "story": {
      "title": "Google Login",
      "user_story": "As a user, I want Google login so that I can sign in faster.",
      "acceptance_criteria": [
        "Given Google auth is enabled, when a user clicks login, then Google OAuth starts.",
        "Given Google authentication succeeds, when the callback returns, then the user is signed in.",
        "Given authentication fails, when the provider rejects the request, then the user sees an error message."
      ],
      "story_points": 3,
      "tasks": {"be": ["OAuth callback"], "fe": ["Login button"], "qa": ["Auth tests"]},
      "definition_of_done": ["Acceptance criteria pass."],
      "warnings": []
    },
    "evaluation": {"status": "APPROVED", "issues": [], "revision_instructions": [], "warnings": []}
  }'
```

Preview Slack payload:

```bash
curl -X POST http://127.0.0.1:8000/actions/slack/preview \
  -H "Content-Type: application/json" \
  -d '{
    "story": {
      "title": "Google Login",
      "user_story": "As a user, I want Google login so that I can sign in faster.",
      "acceptance_criteria": [
        "Given Google auth is enabled, when a user clicks login, then Google OAuth starts.",
        "Given Google authentication succeeds, when the callback returns, then the user is signed in.",
        "Given authentication fails, when the provider rejects the request, then the user sees an error message."
      ],
      "story_points": 3,
      "tasks": {"be": ["OAuth callback"], "fe": ["Login button"], "qa": ["Auth tests"]},
      "definition_of_done": ["Acceptance criteria pass."],
      "warnings": []
    },
    "evaluation": {"status": "APPROVED", "issues": [], "revision_instructions": [], "warnings": []}
  }'
```

## 9. Troubleshooting

### `ModuleNotFoundError: No module named 'ai_scrum_master'`

Đảm bảo đang chạy lệnh từ thư mục gốc:

```bash
cd D:/Antigravity/AI_Agent_PM_PRJ
```

Hoặc set `PYTHONPATH`:

```bash
export PYTHONPATH=D:/Antigravity/AI_Agent_PM_PRJ
```

### Ollama timeout hoặc chậm

Warm up model trước:

```bash
ollama run deepseek-r1:7b "Return only: ok"
```

Sau đó chạy lại API/test.

### RTX 3050 bị OOM hoặc `unable to allocate CPU buffer`

Thông báo `OpenAI API call failed` trong CrewAI thường là log generic của adapter OpenAI-compatible; với config repo này request vẫn trỏ tới Ollama local qua `OLLAMA_BASE_URL`. Lỗi thật là Ollama không load được model.

Dùng model nhỏ hơn và giảm context window:

```bash
ollama pull deepseek-r1:1.5b
export OLLAMA_REASONING_MODEL=deepseek-r1:1.5b
export OLLAMA_NUM_CTX=1024
```

PowerShell:

```powershell
ollama pull deepseek-r1:1.5b
$env:OLLAMA_REASONING_MODEL="deepseek-r1:1.5b"
$env:OLLAMA_NUM_CTX="1024"
```

Đóng app khác đang dùng RAM/VRAM, rồi restart Ollama.

### ChromaDB không có context

Chạy lại ingestion:

```bash
PYTHONPATH=src python -m ai_scrum_master.ingestion.ingest
```

Nếu vẫn không có context, pipeline vẫn chạy nhưng response sẽ có warning như:

```text
No relevant project context found in ChromaDB.
```

## 10. Checklist demo thật

Trước khi demo, chạy đủ checklist này:

```bash
ollama list
python test_crewai_ollama.py
PYTHONPATH=src python -m ai_scrum_master.ingestion.ingest
pytest tests -q
PYTHONPATH=src uvicorn ai_scrum_master.api.main:app --reload --host 127.0.0.1 --port 8000
streamlit run ui/app.py
```

Demo pass khi:

- Ollama trả response thật.
- ChromaDB ingest được ít nhất 1 file.
- Pytest pass.
- `/health` trả `{"status":"ok"}`.
- `/generate` trả story + evaluation + action preview.
- Streamlit mở được trên browser local.
