# AI Scrum Master Agent - Codebase Audit Report

Ngay lap tuc co the dung tai lieu nay lam nen cho proposal ky thuat. Bao cao duoc lap sau khi doc cau truc repo, dependency/config, backend API, Celery worker, LangGraph workflow, agents, RAG ingestion/retrieval, frontend React, test suite va cac artifact phu.

## 1. Tom Tat He Thong

Du an la he thong AI Scrum Master Agent dung de chuyen raw stakeholder requirement thanh Jira-ready work item. He thong co UI React, backend FastAPI, worker bat dong bo Celery, luu lich su MongoDB, RAG tren Qdrant, LangGraph workflow, va local LLM qua Ollama/LangChain ChatOllama adapter.

Gia tri chinh:

- PM/Scrum Master nhap requirement hoac import tai lieu boi canh.
- Researcher Agent tim ngu canh tu vector store.
- Planner Agent tao user story, acceptance criteria, BE/FE/QA tasks, definition of done, story points.
- Evaluator Agent kiem tra chat luong va chan Jira/Slack actions neu output chua dat.
- UI cho phep review, sua draft, tra loi clarification, xu ly oversized split, push Jira, gui Slack, tao GitHub branch.

Trang thai hien tai: code runtime backend compile duoc va frontend build production duoc, nhung test suite va lint dang fail. Can xu ly truoc khi dua vao proposal production-ready.

## 2. Tech Stack Thuc Te

Backend:

- Python 3.11+.
- FastAPI/Starlette/Uvicorn.
- Celery + Redis cho background jobs.
- MongoDB qua `pymongo` de luu projects/history.
- LangGraph cho orchestration.
- LangChain `ChatOllama` adapter goi Ollama cho local LLM.
- LangChain, langchain-qdrant, langchain-ollama cho RAG.
- Qdrant vector database.
- PyMuPDF/fitz, python-docx, pypdf, Typer cho document parsing.
- Pydantic cho schema validation.

Frontend:

- React 19 + Vite 8.
- Tailwind CSS.
- react-i18next/i18next.
- Material Symbols duoc dung truc tiep bang class CSS.

Deployment:

- `docker-compose.yml` chay 6 service: `api`, `worker`, `ui`, `mongodb`, `qdrant`, `redis`.
- Docker Compose dung `src/Dockerfile` cho backend/worker va `frontend/Dockerfile` cho UI.

## 3. Kien Truc Runtime

Entry points chinh:

- Backend app: `src/ai_scrum_master/api/main.py`.
- Generate router: `src/ai_scrum_master/api/routers/generate.py`.
- Celery worker: `src/ai_scrum_master/worker/tasks.py`.
- Pipeline facade: `src/ai_scrum_master/core/pipeline/orchestrator.py`.
- LangGraph workflow: `src/ai_scrum_master/workflows/graph_pipeline.py`.
- Frontend app: `frontend/src/App.jsx`.

Luon generate:

1. UI goi `POST /api/generate`.
2. FastAPI tao Celery task `generate_story_task` va tra `job_id`.
3. UI polling `GET /api/generate/status/{job_id}` moi 2 giay.
4. Worker goi `generate_story_pipeline`.
5. Pipeline goi `run_graph_pipeline`.
6. LangGraph chay:
   - `analyzer`: RouterAgent phan loai domain/story_type/tech_stack/search keywords.
   - `researcher`: tim context tu Qdrant/LangChain.
   - `merge_context`: chon context cho route.
   - `planner`: tao story bang LLM va normalize output.
   - `planner_quality`: deterministic quality gate.
   - `evaluator`: rule-based + optional LLM evaluation.
   - `finalize_approved` hoac `finalize_revision`/`finalize_clarification`/`needs_context`.
7. Ket qua duoc luu MongoDB history.
8. UI hien story draft, evaluation, actions.

Luon ingest:

1. UI upload `.pdf/.docx/.txt/.md` qua `POST /api/ingest/upload`.
2. API luu file vao temp dir.
3. Celery task `ingest_docs_task` parse va chunk tai lieu.
4. Chunk duoc embed bang Ollama embedding model va upsert vao Qdrant.
5. UI polling `/api/ingest/status/{job_id}`.

Luon action:

- Jira preview/execute: `JiraTool`.
- Slack preview/execute: `SlackTool`.
- GitHub branch creation: `GithubTool`, duoc goi trong `execute_all_actions` neu cau hinh GitHub ton tai va Jira tao issue thanh cong.

## 4. Module Map

Backend modules:

- `api/`: FastAPI app, routers cho generate/history/projects/sprint/dashboard.
- `worker/`: Celery app va tasks.
- `workflows/`: LangGraph state va workflow.
- `agents/`: Router, Researcher, Planner, Evaluator.
- `retrieval/`: Qdrant vector store, LangChain RAG, grounded answer utility.
- `ingestion/`: document loading, chunking, universal parser.
- `core/config/`: settings va domain profiles.
- `core/pipeline/`: context selection, finalizer, route builder, orchestration facade.
- `core/validation/`: quality gates, story validation, grounded generation validation.
- `core/llm/`: prompt renderer, LLM setup, JSON extraction utilities.
- `actions/`: Jira, Slack, GitHub integrations.
- `evaluation/` va `datasets/`: benchmark/evaluation tooling, khong phai runtime web path.

Frontend modules:

- `App.jsx`: navigation, project state, generate polling, action handlers.
- `lib/api.ts`: API client cho generate/ingest/history/sprint/projects/dashboard.
- `components/RequirementInputPanel.jsx`: requirement form va upload docs.
- `components/ProcessingStatusPanel.jsx`: stage status.
- `components/StoryDraftEditor.jsx`: edit story, clarification, execute actions.
- `components/StorySplitManagerModal.jsx`: generate/push split stories.
- `components/HistoryPanel.jsx`: history view.
- `components/SprintBoardPanel.jsx`: Jira sprint board, drag/drop status.
- `components/DashboardPanel.jsx`, `AnalyticsPanel.jsx`, `TeamPanel.jsx`: management views.
- Config panels: Jira, Slack, GitHub.

## 5. Tinh Trang Kiem Tra

Da chay:

- `python -m compileall -q src`: pass.
- `npm run build` trong `frontend`: pass.
- `pytest -q`: fail trong test collection.
- `npm run lint`: fail.

Ket qua chi tiet:

- Pytest fail vi tests import cac duong dan cu: `ai_scrum_master.core.http_client`, `core.agent_schemas`, `core.llm_json`, `core.quality`, `core.quality_gate`, `core.domain_profiles`, `core.prompts`, `core.generation_quality`, `scripts.rag_quality`.
- Test architecture da duoc cap nhat theo huong runtime dung `core/pipeline/orchestrator.py` va `workflows/graph_pipeline.py`, khong con legacy agent framework cu.
- Frontend lint fail vi:
  - `App.jsx` dung `fetchSprintBoard` nhung chua import.
  - Nhieu `React` imports khong dung.
  - Mot so state nhu `loading`, `ingestData` khong dung.
  - React hooks lint can sua `setState` trong effect va dependency issues.
  - `i18n.js` va `vite.config.js` thieu global config cho `process`.

## 6. Diem Manh

- Kien truc tach lop kha ro: API, worker, workflow, agents, validation, actions.
- Generate/ingest la async job nen UI khong bi block khi LLM/RAG chay lau.
- Co quality gate deterministic truoc khi push Jira/Slack.
- Co project-level config cho Jira/Slack/GitHub trong MongoDB.
- Co RAG ingestion tu nhieu dinh dang tai lieu.
- Co retry/co che chan action khi story chua approved.
- Frontend build production thanh cong.
- Co benchmark/evaluation assets de chung minh chat luong neu duoc chuan hoa lai.

## 7. Rui Ro Va No Ky Thuat

Rui ro cao:

- Test suite khong chay duoc do refactor module path chua dong bo.
- Runtime LLM setup da chuyen sang `langchain_ollama.ChatOllama`; can tiep tuc verify tren Docker voi Ollama that.
- `.env.example` o `src/ai_scrum_master` con nhieu bien Chroma cu (`CHROMA_*`, `RAG_FALLBACK_TO_DIRECT_CHROMA`) trong khi runtime dang dung Qdrant (`QDRANT_URL`, `QDRANT_COLLECTION`, `RAG_FALLBACK_TO_DIRECT_QDRANT`).
- README va mot so UI text bi mojibake/encoding loi, anh huong chat luong proposal/demo.
- `data/llm_logs/*.json` dang duoc track nhieu file log sinh ra, khong nen nam trong source control.

Rui ro trung binh:

- `context_selector.py` hien comment "Do not filter" va de trong `missing_required_sources`, lam co che required source/domain route yeu hon so voi thiet ke ban dau.
- `SearchContext` co `project_id` tham so nhung ingestion metadata hien khong set `project_id`, do do isolation theo project chua that su chat.
- `execute_all_actions` dung `SlackTool()` thay vi `SlackTool.from_project(project_id)`, nen Slack co the khong lay project-level config.
- `api/main.py` co duplicate imports va mixed responsibilities: app setup, ingest endpoints, action endpoints nam chung.
- Root `Dockerfile` co kha nang stale vi compose dang dung `src/Dockerfile`.
- Root `package.json`/`package-lock.json` co ve la leftover, khong co script runtime; frontend co package rieng.

Rui ro thap:

- Co nhieu benchmark/data scripts o root `data/`, tot cho R&D nhung nen tach khoi production bundle.
- `frontend/src/components/*.html` va `frontend/temp_history.html` co ve la design/static prototypes, khong duoc import runtime.
- `frontend/src/assets/react.svg`, `vite.svg`, `hero.png` khong thay duoc import runtime.

## 8. File/Folder Co The Clear Hoac Tach Khoi Runtime

Khong nen xoa ngay neu chua confirm, nhung day la danh sach ung vien.

Co the xoa/ignore an toan:

- `__pycache__/`, `tests/__pycache__/`, `src/**/__pycache__/`.
- `.pytest_cache/`, `.pytest_tmp/`, `test_tmp/`.
- `frontend/dist/` sau build.
- `src/ai_scrum_master.egg-info/`.
- `data/llm_logs/*.json` nen remove khoi git va ignore.

Prototype/static khong duoc import:

- `frontend/temp_history.html`.
- `frontend/src/components/Analytics.html`.
- `frontend/src/components/Dashboard.html`.
- `frontend/src/components/Team.html`.
- `frontend/src/assets/react.svg`.
- `frontend/src/assets/vite.svg`.
- `frontend/src/assets/hero.png`.

Artifact/manual test nen archive hoac xoa neu khong con can:

- `debug.py`.
- `logs.txt`.
- `output_temp.txt`.
- `payload.json`.
- `oversized_validation_output.json`.
- `pipeline_validation_output.json`.
- `evaluator_diff.txt`.

Can danh gia truoc khi xoa:

- Root `Dockerfile`: compose khong dung, nhung co the dang duoc dung trong CI/manual deployment.
- Root `package.json` va `package-lock.json`: co ve khong phuc vu runtime vi frontend co package rieng.
- `data/*.json` va `data/*.py`: la benchmark/evaluation assets. Khong nen xoa neu proposal can chung minh evaluation, nhung nen tach thanh `benchmarks/` hoac archive.
- `src/ai_scrum_master/evaluation/*.json`: report benchmark, nen giu neu dung lam evidence proposal.

Khong nen xoa:

- `src/ai_scrum_master/data/raw_docs/*`: la default RAG docs.
- `src/ai_scrum_master/prompts/*.md`: runtime prompt templates.
- `src/ai_scrum_master/config/**/*.yaml`: runtime profiles.
- `src/ai_scrum_master/data/swe_bench_sample/*`: tests/datasets co tham chieu.

## 9. De Xuat Cho Proposal

Nen trinh bay voi khach hang theo 3 lop:

1. Business workflow:
   - Nhap yeu cau.
   - Nap tai lieu noi bo.
   - AI phan tich ngu canh.
   - Sinh story/task/DoD.
   - Human review.
   - Day sang Jira/Slack/GitHub.

2. Technical architecture:
   - Local-first AI/Ollama de giam data leakage.
   - Async worker de xu ly tac vu LLM nang.
   - RAG/Qdrant de grounding tren tai lieu noi bo.
   - LangGraph multi-agent co quality gates.
   - Integration layer tach Jira/Slack/GitHub.

3. Delivery roadmap:
   - Phase 1: stabilize build/test/lint, sync env/docs, clean repo.
   - Phase 2: harden multi-project RAG isolation, secrets/security, observability.
   - Phase 3: improve evaluation dashboard va benchmark evidence.
   - Phase 4: production deployment, CI/CD, monitoring, permission model.

## 10. Viec Nen Lam Tiep Theo

Uu tien 1:

- Dong bo test imports voi module moi hoac tao compatibility shims co chu dich.
- Sua frontend lint critical: `fetchSprintBoard` import, unused imports, hooks dependency.
- Cap nhat `requirements.txt`/`pyproject.toml` de khop runtime (`pymongo`/`requests` neu can khai bao truc tiep).
- Cap nhat `.env.example` va README sang Qdrant/Ollama hien tai, sua encoding.
- Remove/untrack generated logs/cache/build artifacts.

Uu tien 2:

- Tach benchmark/evaluation data khoi runtime app package.
- Lam ro project-level document isolation trong Qdrant metadata.
- Dung `SlackTool.from_project(project_id)` trong execute-all.
- Tach `api/main.py` endpoints thanh routers rieng cho ingest/actions.

Uu tien 3:

- Them smoke test cho Docker Compose.
- Them e2e frontend/API happy path co mock LLM.
- Them security note: token storage, secret redaction, auth/role model.
