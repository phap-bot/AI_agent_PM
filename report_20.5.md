#  20.5 — AI Scrum Master Agent Build Summary

Date: 2026-05-20

## 1. Executive Summary

Hôm nay đã chuyển dự án từ tài liệu ý tưởng sang một codebase MVP có cấu trúc rõ ràng cho AI Scrum Master Agent.

Đã hoàn thành 3 lớp chính:

1. **Claude project kit** để điều phối cách build dự án.
2. **Backend MVP skeleton** với FastAPI, agent pipeline, RAG ingestion, Planner/Evaluator LLM fallback, và Jira/Slack preview layer.
3. **Test suite nền tảng** với 19 tests pass, kiểm tra planner, evaluator, ingestion, action tools và backend endpoints ở mức unit/direct-call.

Pipeline hiện tại:

```text
Raw requirement
-> ResearcherAgent
-> PlannerAgent
-> EvaluatorAgent
-> Jira/Slack action preview
-> API response
```

Trạng thái quan trọng: **Jira/Slack hiện mới ở preview mode, chưa gọi API thật**. Điều này là chủ đích để đảm bảo an toàn trước khi có credentials và quyền external execution.

---

## 2. Tech Stack Đã Chốt

Theo `prompt.md` và `.claude/CLAUDE.md`, stack hiện tại gồm:

| Layer | Tech | Trạng thái |
|---|---|---|
| Backend API | FastAPI | Đã scaffold và có endpoints |
| Agent orchestration | Python class pipeline, chuẩn bị cho CrewAI | Có skeleton pipeline; chưa dùng CrewAI task/agent thật |
| LLM runtime | Ollama local | Đã có config/build function; chưa chy end-to-end với model tạhật |
| Reasoning model | `deepseek-r1:7b` | Đã cấu hình default |
| Embedding model | `nomic-embed-text` | Đã cấu hình default |
| Vector store | ChromaDB persistent local | Đã có wrapper và ingestion pipeline |
| Demo UI | Streamlit | Mới placeholder |
| Jira integration | Jira REST payload preview | Đã có payload builder; chưa execute thật |
| Slack integration | Slack webhook payload preview | Đã có message builder; chưa execute thật |
| Testing | pytest | 19 tests pass |
| Package manager | Poetry | Đã có setup commands |
| Hardware constraint | RTX 3050 4GB VRAM | Đã reflect trong Ollama defaults/comment |

---

## 3. Project Structure Hiện Tại

Code chính nằm tại:

```text
ai_scrum_master/
├── api/
│   ├── main.py
│   └── schemas.py
├── agents/
│   ├── researcher.py
│   ├── planner.py
│   ├── evaluator.py
│   ├── crew.py
│   └── tools/
│       ├── jira_tool.py
│       └── slack_tool.py
├── core/
│   ├── config.py
│   ├── llm_setup.py
│   └── vector_store.py
├── ingestion/
│   ├── __init__.py
│   └── ingest.py
├── data/
│   ├── raw_docs/
│   └── chromadb/
├── docs/
│   └── requirements.md
├── tests/
│   ├── test_action_tools.py
│   ├── test_api.py
│   ├── test_evaluator.py
│   ├── test_ingest.py
│   └── test_planner.py
├── evaluation/
│   └── evaluate_metrics.py
├── ui/
│   └── app.py
├── .env
├── .gitignore
├── poetry_setup.md
└── scaffold.sh
```

Ngoài ra có bộ Claude kit:

```text
.claude/
├── CLAUDE.md
├── skills/
├── workflows/
├── templates/
├── specs/
└── playbooks/
```

---

## 4. Claude Kit Đã Build

### 4.1 Mục tiêu

Tạo bộ điều phối chuyên biệt cho dự án AI Scrum Master Agent, gồm slash-style skills, workflows, templates, specs và playbooks.

### 4.2 Thành phần

Đã tạo:

- 19 skills
- 6 workflows
- 8 templates
- 5 specs
- 5 playbooks

### 4.3 Skills nổi bật

| Slash | Vai trò |
|---|---|
| `/pipeline-architect` | Rút pipeline từ tài liệu |
| `/story-write` | Viết user story, AC, SP, tasks |
| `/story-eval` | Đánh giá story quality |
| `/clarify-request` | Hỏi lại khi request mơ hồ |
| `/split-sprint-scope` | Chia scope lớn thành nhiều story/sprint |
| `/rag-design` | Thiết kế RAG/ChromaDB |
| `/repo-scaffold` | Tạo project skeleton |
| `/poetry-setup` | Sinh lệnh Poetry setup |
| `/ollama-runtime` | Cấu hình Ollama an toàn cho VRAM thấp |
| `/vector-store-setup` | Thiết kế ChromaDB + embedding |
| `/jira-action` | Thiết kế Jira payload/action |
| `/slack-notify` | Thiết kế Slack notification |
| `/eval-harness` | Thiết kế benchmark/test |
| `/failure-playbook` | Chuẩn hóa fallback/retry/escalation |

### 4.4 Trạng thái apply thật

| Phần | Đã apply thật? | Ghi chú |
|---|---:|---|
| `.claude/CLAUDE.md` | Có | Đã phản ánh mission, stack, rules |
| Skills/workflows/templates | Có | Là file hướng dẫn/điều phối, không phải runtime code |
| Cascade skills | Một phần | Đã có chain trong workflows; chưa có automation gọi skill tự động |

---

## 5. Backend API Đã Build

File chính:

- `ai_scrum_master/api/main.py`
- `ai_scrum_master/api/schemas.py`

### 5.1 Endpoints hiện có

#### `GET /health`

Trạng thái: **hoạt động ở code level**

Mục đích:

```json
{"status": "ok"}
```

#### `POST /generate`

Trạng thái: **hoạt động ở backend pipeline level**

Input:

```json
{
  "requirement": "Add Google login",
  "n_results": 5
}
```

Output gồm:

```json
{
  "context": {},
  "story": {},
  "evaluation": {},
  "actions": {
    "jira": {},
    "slack": {}
  }
}
```

Luồng bên trong:

```text
ScrumMasterCrew.run()
-> ResearcherAgent.run()
-> PlannerAgent.run()
-> EvaluatorAgent.run()
-> _prepare_actions()
```

#### `POST /ingest`

Trạng thái: **đã build endpoint + test với fake runner**

Mục đích:

- Nhận folder raw docs.
- Gọi ingestion pipeline.
- Trả số file/chunk đã index.

Input:

```json
{
  "raw_docs_dir": "ai_scrum_master/data/raw_docs",
  "collection_name": "project_context"
}
```

#### `POST /actions/jira/preview`

Trạng thái: **preview only**

Mục đích:

- Nhận story + evaluation.
- Nếu `evaluation.status != APPROVED`, block action.
- Nếu approved, build Jira payload.
- Không gọi Jira thật.

#### `POST /actions/slack/preview`

Trạng thái: **preview only**

Mục đích:

- Nhận story + evaluation.
- Nếu `evaluation.status != APPROVED`, block action.
- Nếu approved, build Slack message payload.
- Không gửi webhook thật.

---

## 6. Agent Pipeline Đã Build

File:

- `ai_scrum_master/agents/crew.py`

### 6.1 Current pipeline

```python
context = researcher.run(requirement)
story = planner.run(requirement, context)
evaluation = evaluator.run(story)
actions = _prepare_actions(story, evaluation)
```

### 6.2 Trạng thái kỹ thuật

| Component | Trạng thái | Ghi chú |
|---|---|---|
| `ResearcherAgent` | Có retrieval wrapper | Cần test end-to-end với Chroma thật |
| `PlannerAgent` | Có LLM mode + fallback | Chưa kiểm output thật từ deepseek-r1:7b |
| `EvaluatorAgent` | Có rule check + LLM mode + fallback | Rule check hiện là quality gate chính |
| `ScrumMasterCrew` | Có orchestration đơn giản | Chưa dùng CrewAI Agent/Task/Crew object thật |

### 6.3 Phần cần apply thật

- Chạy Ollama thật.
- Pull model `deepseek-r1:7b`.
- Pull embedding model `nomic-embed-text`.
- Ingest tài liệu thật vào ChromaDB.
- Gọi `/generate` end-to-end với request thật.
- Đánh giá output LLM thật có parse JSON ổn định không.

---

## 7. RAG / Ingestion Đã Build

Files:

- `ai_scrum_master/ingestion/ingest.py`
- `ai_scrum_master/core/vector_store.py`
- `ai_scrum_master/agents/researcher.py`

### 7.1 Ingestion pipeline

Đã hỗ trợ:

- Đọc `.md` và `.txt` trong `data/raw_docs`.
- Chunk text với overlap.
- Tạo chunk id bằng SHA1.
- Ghi metadata:
  - `source`
  - `chunk_index`
  - `file_type`
- Gọi `add_documents()` để add vào ChromaDB.

### 7.2 Vector store

Đã hỗ trợ:

- Persistent ChromaDB path: `data/chromadb/`
- Embedding function qua Ollama:
  - URL default: `http://localhost:11434`
  - model: `nomic-embed-text`
- Query include:
  - documents
  - metadatas
  - distances

### 7.3 Researcher output

`ResearcherAgent` hiện trả:

```json
{
  "documents": [],
  "ids": [],
  "metadatas": [],
  "distances": [],
  "confidence": 0.0,
  "warnings": []
}
```

### 7.4 Trạng thái apply thật

| Phần | Trạng thái |
|---|---|
| Chunking | Đã test |
| Ingest endpoint | Đã test bằng fake runner |
| ChromaDB real write | Chưa test thật trong phase này |
| Ollama embedding real call | Chưa test thật |
| Retrieval quality | Chưa benchmark |

---

## 8. Planner Đã Build

File:

- `ai_scrum_master/agents/planner.py`

### 8.1 Chức năng

Planner hiện có:

- Build prompt từ requirement + retrieved context.
- Gọi LLM qua `build_llm()`.
- Ép output JSON.
- Parse JSON kể cả khi LLM bọc trong markdown code block.
- Normalize thiếu field.
- Kiểm story points phải thuộc Fibonacci.
- Fallback story nếu LLM lỗi hoặc Ollama chưa sẵn sàng.

### 8.2 Fallback behavior

Nếu LLM lỗi:

```text
Planner LLM unavailable; used fallback story.
```

### 8.3 Trạng thái apply thật

| Phần | Trạng thái |
|---|---|
| Prompt và parser | Đã build |
| Unit tests với fake LLM | Đã pass |
| Gọi deepseek-r1:7b thật | Chưa test |
| Output quality thật | Chưa benchmark |
| Ambiguous request detection | Chưa tách thành logic riêng trong runtime |
| Oversized request splitting | Chưa tách thành logic riêng trong runtime |

---

## 9. Evaluator Đã Build

File:

- `ai_scrum_master/agents/evaluator.py`

### 9.1 Chức năng

Evaluator hiện có 2 lớp:

1. **Rule-based pre-check**
2. **LLM evaluator**

Rule check kiểm:

- User story có `As a / I want / so that`
- Có ít nhất 3 acceptance criteria
- Mỗi AC có `Given / When / Then`
- Story points thuộc Fibonacci
- Tasks có đủ `be`, `fe`, `qa`

### 9.2 Rule override LLM

Nếu rule check báo `REVISION`, nhưng LLM trả `APPROVED`, hệ thống vẫn giữ `REVISION`.

Đây là behavior đúng vì action layer không được phép bypass evaluator/rule quality gate.

### 9.3 Trạng thái apply thật

| Phần | Trạng thái |
|---|---|
| Rule evaluator | Đã build/test |
| LLM evaluator prompt | Đã build/test với fake LLM |
| Gọi LLM thật | Chưa test |
| Revision loop tối đa 3 rounds | Chưa implement runtime loop |
| Escalate PM sau 3 revisions | Chưa implement runtime action |

---

## 10. Jira Tool Đã Build

File:

- `ai_scrum_master/agents/tools/jira_tool.py`

### 10.1 Chức năng hiện có

- `JiraConfig`
- `JiraTool`
- `build_story_payload(story)`
- `build_subtask_payloads(parent_key, story)`
- `prepare_action(story)`

### 10.2 Payload story hiện có

Payload gồm:

- project key
- summary
- description
- issue type: Story
- labels: `ai-scrum-master`

### 10.3 Payload subtask hiện có

Subtask được build từ tasks:

- BE
- FE
- QA

Format summary:

```text
[BE-001] Task name
[FE-001] Task name
[QA-001] Task name
```

### 10.4 Trạng thái apply thật

| Phần | Trạng thái |
|---|---|
| Build Jira payload | Đã build/test |
| Preview endpoint | Đã build/test |
| Jira REST POST thật | Chưa build |
| Auth Basic/API token | Chưa build |
| Retry 401 up to 3 | Chưa build |
| Partial failure handling | Chưa build |
| Real Jira field mapping | Chưa xác nhận |

### 10.5 Cần config để chạy thật

```env
JIRA_BASE_URL=
JIRA_PROJECT_KEY=
JIRA_EMAIL=
JIRA_API_TOKEN=
```

---

## 11. Slack Tool Đã Build

File:

- `ai_scrum_master/agents/tools/slack_tool.py`

### 11.1 Chức năng hiện có

- `SlackConfig`
- `SlackTool`
- `build_story_message(story, evaluation)`
- `prepare_action(story, evaluation)`

### 11.2 Message preview hiện có

Payload gồm:

- `text`
- Slack `blocks`
- story title
- user story
- evaluator status
- story points

### 11.3 Trạng thái apply thật

| Phần | Trạng thái |
|---|---|
| Build Slack payload | Đã build/test |
| Preview endpoint | Đã build/test |
| Webhook POST thật | Chưa build |
| Retry transient failure | Chưa build |
| Message formatting final | Chưa refine |

### 11.4 Cần config để chạy thật

```env
SLACK_WEBHOOK_URL=
```

---

## 12. Config / Environment Đã Build

File:

- `ai_scrum_master/core/config.py`

Đã hỗ trợ env:

```env
APP_NAME=
APP_VERSION=
OLLAMA_BASE_URL=
OLLAMA_REASONING_MODEL=
OLLAMA_EMBED_MODEL=
CHROMA_PERSIST_DIR=
CHROMA_COLLECTION=
JIRA_BASE_URL=
JIRA_PROJECT_KEY=
JIRA_EMAIL=
JIRA_API_TOKEN=
SLACK_WEBHOOK_URL=
```

### Trạng thái

- Config reader đã build.
- `.env` file đã tạo nhưng chưa có giá trị thật.
- Chưa có `.env.example`, nên cần thêm ở phase sau.

---

## 13. Tests Đã Build

Test files:

```text
ai_scrum_master/tests/test_action_tools.py
ai_scrum_master/tests/test_api.py
ai_scrum_master/tests/test_evaluator.py
ai_scrum_master/tests/test_ingest.py
ai_scrum_master/tests/test_planner.py
```

### 13.1 Test coverage hiện tại

| Area | Có test? | Ghi chú |
|---|---:|---|
| Planner fallback | Có | Không cần Ollama thật |
| Planner JSON parse | Có | Fake LLM |
| Evaluator rule check | Có | Không cần Ollama thật |
| Evaluator LLM parse | Có | Fake LLM |
| Evaluator fallback | Có | Fake broken LLM |
| Ingestion chunking | Có | Unit test |
| Jira payload | Có | Unit test |
| Slack payload | Có | Unit test |
| API endpoint functions | Có | Direct function call, không dùng TestClient |
| Chroma real integration | Chưa | Cần runtime deps/model |
| Ollama real integration | Chưa | Cần local model |
| Jira real API | Chưa | Cần credentials/quyền |
| Slack real webhook | Chưa | Cần webhook/quyền |

### 13.2 Test output mới nhất

Command:

```bash
python -m pytest "/d/Antigravity/AI_Agent_PM_PRJ/ai_scrum_master/tests"
```

Output:

```text
collected 19 items

ai_scrum_master\tests\test_action_tools.py ....    [ 21%]
ai_scrum_master\tests\test_api.py .....            [ 47%]
ai_scrum_master\tests\test_evaluator.py .....      [ 73%]
ai_scrum_master\tests\test_ingest.py ..            [ 84%]
ai_scrum_master\tests\test_planner.py ...          [100%]

19 passed in 0.63s
```

Compile check:

```bash
python -m compileall "/d/Antigravity/AI_Agent_PM_PRJ/ai_scrum_master"
```

Output:

```text
Compiled 1 packages
```

---

## 14. Dependency / Setup Status

File:

- `ai_scrum_master/poetry_setup.md`

Commands hiện tại:

```bash
poetry init --name ai-scrum-master --python "^3.11" --no-interaction
poetry add fastapi uvicorn crewai chromadb streamlit ollama pydantic python-dotenv
poetry add --group dev pytest
```

### Ghi chú kỹ thuật

Môi trường hiện tại đã có một số package đủ để chạy tests, nhưng runtime thật vẫn cần xác nhận bằng Poetry env sạch.

Cần cân nhắc thêm dependencies khi bật real execution:

- `httpx` hoặc `requests` cho Jira/Slack HTTP calls
- `pytest-httpx` hoặc mock transport cho tests HTTP

---

## 15. Phân Loại: Phần Nào Đã Dùng Được, Phần Nào Cần Apply Thật

### 15.1 Đã dùng được ngay ở mức local/unit

- Project structure.
- Backend function-level endpoints.
- Planner fallback.
- Evaluator rule quality gate.
- Jira payload preview.
- Slack payload preview.
- Ingestion chunking.
- Requirements document.
- `.gitignore`.
- Test suite 19 pass.

### 15.2 Đã build nhưng cần runtime thật để xác nhận

- Ollama `deepseek-r1:7b` generation.
- Ollama `nomic-embed-text` embedding.
- ChromaDB persistent add/query.
- FastAPI server runtime via Uvicorn.
- `/generate` end-to-end với model và vector DB thật.

### 15.3 Mới là skeleton/preview, chưa execute thật

- Jira issue creation.
- Jira sub-task creation.
- Jira 401 refresh/retry.
- Slack webhook POST.
- Human approval UI.
- Streamlit demo UI.
- CrewAI-native Agent/Task/Crew orchestration.
- Revision loop tối đa 3 lần.
- Ambiguous request classifier.
- Oversized scope splitter runtime.

---

## 16. Những Điểm Kỹ Thuật Cần Lưu Ý

### 16.1 TestClient issue đã xử lý

Ban đầu `fastapi.testclient.TestClient` fail do mismatch giữa `starlette` và `httpx` trong môi trường hiện tại.

Giải pháp hiện tại:

- Test API bằng direct function call.
- Dùng dependency injection cho crew, ingest runner, JiraTool, SlackTool.

Điều này giúp test ổn định mà chưa cần fix dependency tree.

### 16.2 Lazy import đã thêm

`crewai` và `chromadb` được lazy import để unit tests không fail nếu runtime deps chưa cài đầy đủ.

Files liên quan:

- `core/llm_setup.py`
- `core/vector_store.py`

### 16.3 Action safety

Jira/Slack không gửi thật.

Action layer chỉ trả preview payload và `ready` status.

---

## 17. Phase Cần Tiếp Tục Build

### Phase B — Real Jira/Slack Execution With Mock Tests

Mục tiêu: Bật execution thật có kiểm soát, nhưng test bằng mock HTTP trước khi dùng credentials thật.

#### Cần build

1. Thêm HTTP client abstraction:
   - `core/http_client.py` hoặc inject `httpx.Client` vào tools.
2. Jira real sender:
   - `POST {JIRA_BASE_URL}/rest/api/3/issue`
   - Basic auth bằng email + API token.
   - Create Story trước.
   - Lấy issue key.
   - Create Sub-tasks sau.
3. Retry policy:
   - 401 -> refresh/auth retry placeholder hoặc clear escalation.
   - 429/5xx -> retry tối đa 3 lần.
   - partial failure -> trả created issue + failed subtasks.
4. Slack real sender:
   - POST webhook.
   - Retry transient failure.
   - Return status + response metadata.
5. Backend endpoints:
   - `POST /actions/jira/execute`
   - `POST /actions/slack/execute`
   - `POST /actions/execute-all`
6. Tests:
   - Mock Jira success.
   - Mock Jira 401/failure.
   - Mock Slack success.
   - Mock Slack failure.
   - Ensure execution blocked if evaluation != APPROVED.

#### Cần quyền/config

```env
JIRA_BASE_URL=
JIRA_PROJECT_KEY=
JIRA_EMAIL=
JIRA_API_TOKEN=
SLACK_WEBHOOK_URL=
```

Ban đầu chưa cần credential thật nếu test bằng mock HTTP.

---

### Phase C — Real RAG Runtime Verification

Mục tiêu: Xác nhận ingestion và retrieval thật với ChromaDB + Ollama embedding.

#### Cần build/apply

1. Thêm `.env.example`.
2. Thêm sample docs trong `data/raw_docs/`.
3. Chạy:

```bash
ollama pull nomic-embed-text
python ai_scrum_master/ingestion/ingest.py
```

4. Test query thật với `ResearcherAgent`.
5. Thêm integration test optional, có marker như:

```text
@pytest.mark.integration
```

#### Output cần đạt

- ChromaDB folder có dữ liệu.
- Query trả documents/metadatas/distances.
- Confidence không còn 0 nếu context match.

---

### Phase D — Real LLM Planner/Evaluator Verification

Mục tiêu: Kiểm deepseek-r1:7b chạy ổn trên RTX 3050 4GB VRAM.

#### Cần làm

1. Chạy:

```bash
ollama pull deepseek-r1:7b
```

2. Smoke test `build_llm()`.
3. Gọi Planner với fake context thật.
4. Kiểm JSON parse robustness.
5. Nếu output hay bị thêm reasoning text, cần thêm extractor/parser mạnh hơn.
6. Tune:
   - `OLLAMA_NUM_CTX`
   - `OLLAMA_TIMEOUT`
   - model quantization nếu OOM.

#### Output cần đạt

- Planner trả valid JSON.
- Evaluator trả valid JSON.
- Fallback không bị kích hoạt trong happy path.

---

### Phase E — Streamlit Demo UI

Mục tiêu: Có demo UI để PM nhập requirement và xem story/evaluation/action preview.

#### Cần build

1. Input textarea cho requirement.
2. Button `Generate`.
3. Hiển thị:
   - retrieved context
   - confidence/warnings
   - story draft
   - evaluator status
   - Jira preview
   - Slack preview
4. Human approval controls:
   - Approve
   - Request revision
   - Edit story fields
5. Sau Phase B, thêm execute buttons:
   - Send to Jira
   - Notify Slack

---

### Phase F — Runtime Revision Loop

Mục tiêu: Implement đúng rule revision loop tối đa 3 lần.

#### Cần build

1. Nếu evaluator trả `REVISION`, gửi `revision_instructions` về Planner.
2. Planner regenerate tối đa 3 lần.
3. Nếu vẫn fail:
   - status escalate
   - không action Jira/Slack
   - tạo warning cho PM.
4. Tests:
   - approved round 1
   - revision then approved round 2
   - revision 3 lần -> escalate

---

### Phase G — Ambiguity and Oversized Scope Runtime

Mục tiêu: Đưa các rule trong tài liệu gốc vào runtime.

#### Cần build

1. Ambiguity detector:
   - request quá ngắn
   - thiếu module
   - thiếu expected behavior
   - performance vague như "app chậm"
2. Clarification questions generator.
3. Oversized scope detector:
   - nhiều payment methods
   - nhiều modules
   - nhiều workflow verbs
4. Splitter:
   - tạo nhiều stories
   - tính tổng story points
   - đề xuất sprint allocation.
5. Update schemas để hỗ trợ `stories: list`, không chỉ single story.

---

## 18. Recommended Next Step

Khuyến nghị tiếp theo: **Phase B — Real Jira/Slack Execution With Mock Tests**.

Lý do:

- Action preview đã có.
- Payload builder đã test.
- Đây là bước tự nhiên để biến preview thành action thật.
- Có thể build bằng mock tests trước, chưa cần credentials thật.

Sau khi Phase B pass test bằng mock HTTP, mới cần bạn cấp credential hoặc quyền gọi external thật để smoke test live.

---

## 19. Current Quality Gate

Trước khi chuyển phase, trạng thái hiện tại đạt:

- Code compile pass.
- 19 tests pass.
- Không gọi external service ngoài ý muốn.
- Jira/Slack bị block nếu evaluator chưa `APPROVED`.
- Secrets chưa hardcode.
- Local vector data và `.env` đã được ignore.

Kết luận: Phase A đã hoàn thành ở mức kỹ thuật tốt để tiếp tục Phase B.