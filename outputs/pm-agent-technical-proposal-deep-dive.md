# Technical Proposal: PM-Agent / AI Scrum Master

## 1. Tóm tắt đề xuất

PM-Agent là công cụ hỗ trợ PM/PO/Scrum Master chuyển yêu cầu thô từ stakeholder thành bản nháp work item có cấu trúc, có kiểm tra chất lượng và có cơ chế chặn trước khi đồng bộ sang Jira/Slack/GitHub.

Ở trạng thái codebase hiện tại, hệ thống được triển khai theo hướng **local-first AI workflow**:

- Frontend: React/Vite/Tailwind.
- Backend API: FastAPI.
- Background job: Celery + Redis.
- Orchestration: LangGraph.
- LLM runtime: Ollama local.
- Vector database: Qdrant.
- Storage/config/history: MongoDB.
- Integrations: Jira, Slack, GitHub.

Điểm quan trọng: code hiện tại đang dùng **LangGraph + Qdrant + React**, không phải CrewAI + ChromaDB + Streamlit như một số mô tả ban đầu.

---

## 2. Mục tiêu kỹ thuật của hệ thống

Hệ thống được thiết kế để giải quyết 5 việc chính:

1. Nhận yêu cầu từ user hoặc stakeholder.
2. Tìm context liên quan từ tài liệu đã ingest.
3. Sinh user story, acceptance criteria, story points, task BE/FE/QA và definition of done.
4. Đánh giá output có đủ điều kiện sprint-ready không.
5. Chỉ cho phép action Jira/Slack/GitHub khi output đã đạt điều kiện.

Luồng chính:

```text
Input
→ Analyzer / Router
→ Researcher
→ Context Selector
→ Planner
→ Planner Quality Gate
→ Evaluator
→ Finalizer
→ Human Review
→ Jira / Slack / GitHub Action
```

---

## 3. Embedding và Knowledge Retrieval

### 3.1 Embedding dùng kỹ thuật gì?

Hệ thống dùng kỹ thuật **text embedding + vector search** để biến tài liệu nội bộ thành vector, sau đó tìm các đoạn tài liệu gần nghĩa với yêu cầu của user.

Trong code hiện tại:

- Embedding được tạo qua `langchain_ollama.OllamaEmbeddings`.
- Model mặc định lấy từ biến môi trường `OLLAMA_EMBED_MODEL`.
- Default trong settings hiện tại là `bge-m3`.
- Vector store là Qdrant.

Luồng embedding:

```text
Document
→ parse text
→ normalize text
→ split/chunk
→ embed chunk bằng OllamaEmbeddings
→ upsert vào Qdrant
```

### 3.2 Model embedding là gì?

Theo code hiện tại:

```text
Default embedding model: bge-m3
Config key: OLLAMA_EMBED_MODEL
Runtime: Ollama local
Vector store: Qdrant
```

Lưu ý: file env mẫu cũ có thể còn nhắc `nomic-embed-text`, nhưng runtime settings hiện tại default là `bge-m3`. Khi triển khai chính thức, cần thống nhất lại `.env.example`, README và deployment config để tránh lệch tài liệu.

### 3.3 Tài liệu được ingest như thế nào?

Module ingestion hỗ trợ các nguồn tài liệu dạng:

- PDF.
- DOCX.
- TXT.
- Markdown.

Quá trình ingest:

1. User upload tài liệu hoặc dùng raw docs có sẵn.
2. Backend/Celery xử lý bất đồng bộ.
3. Tài liệu được parse thành text.
4. Text được chia chunk theo cấu hình:
   - `RAG_CHUNK_SIZE`.
   - `RAG_CHUNK_OVERLAP`.
   - `RAG_MARKDOWN_CHUNK_SIZE`.
   - `RAG_MARKDOWN_CHUNK_OVERLAP`.
5. Mỗi chunk có metadata:
   - source file.
   - chunk index.
   - document hash.
   - chunk hash.
   - project id nếu có.
6. Chunk được embed và lưu vào Qdrant.

### 3.4 Cách tìm context

Khi user gửi requirement, Researcher gọi retrieval theo luồng:

```text
Requirement text
→ compact query
→ search Qdrant bằng vector similarity
→ nếu bật hybrid search: rerank bằng lexical score + vector score
→ chọn top context
→ tạo evidence package cho Planner
```

Hệ thống hiện có hai đường retrieval:

1. **LangChain Qdrant path**
   - Dùng `langchain_qdrant.QdrantVectorStore`.
   - Dùng embedding model của Ollama để search.
   - Có filter theo `project_id` nếu truyền vào.

2. **Direct Qdrant fallback**
   - Nếu LangChain path lỗi và config cho phép fallback.
   - Gọi trực tiếp Qdrant client để query.

### 3.5 Hybrid search hoạt động như thế nào?

Nếu `RAG_HYBRID_SEARCH=true`, hệ thống không chỉ dựa vào vector similarity. Sau khi lấy candidates từ Qdrant, hệ thống tính thêm lexical score.

Ý tưởng:

```text
final_score = 0.35 * vector_score + 0.65 * lexical_score
```

Ngoài ra còn có bonus nếu có phrase match. Điều này giúp các issue kỹ thuật có keyword đặc thù như `MCP`, `agenthost`, `target`, `tool source` không bị chìm hoàn toàn trong embedding semantic.

### 3.6 Forced context

Khi user chọn/import tài liệu cụ thể, Researcher có thể dùng `forced_context_docs`.

Ý nghĩa:

- Không chỉ search toàn bộ collection.
- Ưu tiên tìm chunk trong những file user chỉ định.
- Hữu ích khi user biết tài liệu liên quan nằm trong một file cụ thể, ví dụ `vscode_ai_docs_full.md`.

---

## 4. Analyzer / Router Agent

### 4.1 Vai trò

Analyzer/Router là bước định tuyến ban đầu. Nó xác định request thuộc loại nào để các agent sau không xử lý mù.

Các thông tin route thường gồm:

- Domain.
- Story type.
- Required sources.
- Optional sources.
- Forbidden domains.
- Template/profile name.
- Search keywords.

### 4.2 Tại sao cần Router?

Không phải request nào cũng nên đi thẳng vào Planner.

Ví dụ:

- Request quá mơ hồ → cần clarification.
- Request quá lớn → cần split.
- Request thuộc domain auth → ưu tiên context auth.
- Request thuộc checkout → tránh kéo nhầm context scrum/auth.
- Request benchmark/issue kỹ thuật → cần giữ keyword kỹ thuật.

Router giúp giảm rủi ro Planner tạo story từ context không liên quan.

---

## 5. Researcher Agent

### 5.1 Researcher dùng model gì?

Trong code hiện tại, Researcher có thể dùng model riêng qua:

```text
OLLAMA_RESEARCHER_MODEL
```

Nếu không khai báo, nó fallback theo logic:

```text
OLLAMA_RESEARCHER_MODEL
→ OLLAMA_REASONING_MODEL
→ qwen2.5:3b
```

Tuy nhiên, phần quan trọng của Researcher hiện nay không chỉ là LLM. Researcher chủ yếu dựa vào:

- Qdrant retrieval.
- source matching.
- score threshold.
- evidence ranking.
- context packaging.

### 5.2 Input của Researcher

Researcher nhận:

- requirement.
- số lượng kết quả cần lấy `n_results`.
- route/domain từ Analyzer.
- project id.
- forced context docs nếu user chọn file cụ thể.
- feedback nếu pipeline retry.

### 5.3 Output của Researcher

Researcher trả về một context bundle gồm:

- `documents`.
- `matches`.
- `retrieved_sources`.
- `selected_context_sources`.
- `ignored_context_sources`.
- `context_snippets`.
- `planning_brief`.
- `retrieval_status`.
- `confidence`.
- `raw_match_count`.
- `warnings`.

### 5.4 Researcher đánh giá context như thế nào?

Researcher không chỉ lấy top-k rồi ném cho Planner. Nó còn:

- lọc match dưới threshold.
- giữ evidence có source/domain phù hợp.
- tạo excerpt ngắn.
- đánh dấu retrieval status:
  - ok.
  - empty.
  - failed.
  - no relevant context.
- tạo warning nếu retrieval yếu.

### 5.5 Ý nghĩa với PM workflow

Researcher đóng vai trò giống một BA/PM assistant đọc tài liệu trước:

- Tìm đoạn tài liệu liên quan.
- Cho biết nguồn nào được dùng.
- Báo khi không đủ context.
- Không để Planner bịa chắc chắn khi retrieval yếu.

---

## 6. Planner Agent

### 6.1 Planner dùng model gì?

Planner dùng reasoning model từ:

```text
OLLAMA_REASONING_MODEL
```

Default trong settings hiện tại:

```text
pm-agent
```

LLM adapter:

```text
langchain_ollama.ChatOllama
```

Các runtime option quan trọng:

- `OLLAMA_BASE_URL`.
- `OLLAMA_NUM_CTX`.
- `OLLAMA_NUM_GPU`.
- `OLLAMA_TEMPERATURE`.
- `OLLAMA_TIMEOUT`.

### 6.2 Vì sao Planner cần compact prompt?

Trong thực tế log đã ghi nhận lỗi:

```text
request exceeds the available context size (2048 tokens)
```

Điều này xảy ra khi:

- requirement dài.
- retrieved context dài.
- prompt template dài.
- local model có context window nhỏ.

Do đó Planner hiện đã được điều chỉnh để:

- giảm context block.
- giảm số context item.
- giảm requirement prompt chars.
- dùng compact prompt nếu `OLLAMA_NUM_CTX <= 2048`.
- bỏ few-shot dài khi chạy context nhỏ.

Mục tiêu: tránh local Ollama OOM/context overflow trên máy cấu hình vừa phải.

### 6.3 Planner tạo user story như thế nào?

Planner nhận:

- requirement hiện tại.
- selected retrieved context.
- planning status từ local classifier.
- route/domain.
- context sources.

Sau đó Planner yêu cầu LLM trả về JSON theo schema:

```json
{
  "title": "string",
  "story_type": "software_feature | process_improvement | oversized_request | ambiguous_request",
  "jira_issue_type": "Story | Task | Bug | Epic",
  "jira_labels": ["string"],
  "jira_linked_items": [],
  "user_story": "string",
  "acceptance_criteria": [],
  "story_points": 1,
  "tasks": {
    "be": [],
    "fe": [],
    "qa": []
  },
  "definition_of_done": [],
  "planning_status": "READY | NEEDS_CLARIFICATION | NEEDS_SPLIT | SPLIT_RECOMMENDED | REVISION",
  "clarification_questions": [],
  "assumptions": [],
  "story_splits": [],
  "sprint_allocation": [],
  "context_sources": [],
  "warnings": []
}
```

### 6.4 Cách tạo User Story

Nếu request đủ rõ, Planner tạo story theo format:

```text
As a [user/role],
I want [capability],
so that [business/technical outcome].
```

Planner phải dựa vào:

- requirement.
- context được retrieve.
- domain route.
- assumption nếu context thiếu.

Nếu không xác định được actor, behavior hoặc outcome, Planner không nên ép tạo story mà trả `NEEDS_CLARIFICATION`.

### 6.5 Cách tạo Acceptance Criteria

Acceptance criteria bắt buộc theo format:

```text
Given [context],
When [action],
Then [expected result].
```

Với story READY:

- tối thiểu 3 AC.
- AC phải test được.
- AC không được là template chung chung.
- AC phải liên quan trực tiếp đến requirement hiện tại.

Ví dụ với issue “MCP servers don't appear for agenthost target”:

```text
Given MCP servers are configured as tool sources,
When the user opens the agenthost target,
Then the configured MCP servers are visible as available tools.
```

### 6.6 Cách tạo Definition of Done

Definition of Done không chỉ là “code done”. Nó cần thể hiện điều kiện hoàn tất story.

Với READY story, DoD cần tối thiểu 4 check:

- AC đã pass.
- BE/FE implementation hoàn tất nếu có.
- QA evidence hoặc test scenario đã có.
- edge case/failure case đã được kiểm tra.
- reviewer/PM có thể xác nhận story ready.

Evaluator có chấm điểm DoD theo nhiều dimension, nên DoD quá ngắn hoặc generic sẽ bị revision.

### 6.7 Cách tạo task BE / FE / QA

Planner tách task thành 3 nhóm:

```json
{
  "be": ["backend/server/API/service work"],
  "fe": ["UI/client/display/interaction work"],
  "qa": ["test/validation/regression/UAT work"]
}
```

Nguyên tắc:

- Mỗi nhóm phải có ít nhất 1 task nếu story READY.
- Task phải là action cụ thể, không phải user story trá hình.
- Task không nên quá generic như “Implement backend endpoints”.
- Task phải đúng responsibility group.

Ví dụ:

```text
BE: Inspect agenthost tool-source resolution logic for MCP server entries.
FE: Verify the agenthost target UI renders MCP server tools when returned by backend/tool registry.
QA: Add regression coverage for MCP server visibility under agenthost target configuration.
```

### 6.8 Story point estimation

Story points chỉ được dùng các giá trị Fibonacci:

```text
1, 2, 3, 5, 8, 13
```

Planner dùng Fibonacci vì estimate trong Agile phản ánh:

- complexity.
- uncertainty.
- integration risk.
- test scope.
- coordination effort.

Nếu LLM trả story point không thuộc Fibonacci, hệ thống sẽ reset/null và để quality gate/evaluator xử lý.

### 6.9 Handling ambiguous request

Nếu request mơ hồ, Planner trả:

```text
planning_status = NEEDS_CLARIFICATION
```

Khi đó:

- không tạo user_story READY.
- không tạo AC.
- không story point.
- không BE/FE/QA tasks.
- trả ít nhất 3 clarification questions.

Mục tiêu: không tạo Jira ticket khi input chưa đủ rõ.

### 6.10 Handling oversized request

Nếu request quá lớn cho một sprint, Planner trả:

```text
planning_status = SPLIT_RECOMMENDED
```

hoặc:

```text
planning_status = NEEDS_SPLIT
```

Khi đó Planner phải đề xuất:

- story_splits.
- sprint_allocation.

Parent oversized request không được coi là Jira-ready story.

---

## 7. Planner Quality Gate

Sau Planner, hệ thống có deterministic quality gate trước khi đi tiếp.

Quality gate kiểm tra:

- planning_status hợp lệ.
- READY story có đủ AC.
- AC đúng Given/When/Then.
- story points thuộc Fibonacci.
- tasks có đủ BE/FE/QA.
- DoD đủ số lượng.
- không lẫn domain không liên quan.
- required context/concept có được phản ánh không.

Nếu gate fail, pipeline có thể retry researcher/planner trong giới hạn. Nếu không sửa được, output đi vào revision/human review.

---

## 8. Evaluator Agent

### 8.1 Vai trò

Evaluator là quality gate cuối trước action. Nó trả:

```text
APPROVED
```

hoặc:

```text
REVISION
```

### 8.2 Evaluator đánh giá dựa vào đâu?

Evaluator đánh giá dựa vào:

1. Rule-based validation trong code.
2. Story output từ Planner.
3. Planning status.
4. Requirement hiện tại.
5. Route/domain.
6. Retrieved context/context sources.
7. Optional LLM evaluation nếu bật.

Điểm quan trọng: rule-based validation có thể override LLM. Nếu LLM nói approved nhưng rule fail, hệ thống vẫn trả REVISION.

### 8.3 Các tiêu chí Evaluator kiểm tra với READY story

Evaluator kiểm tra:

- User story có đủ `As a / I want / so that`.
- Có ít nhất 3 acceptance criteria.
- Mỗi AC có Given/When/Then đúng thứ tự.
- AC không generic.
- Story points thuộc Fibonacci.
- Có task BE.
- Có task FE.
- Có task QA.
- Task đủ actionable.
- Task không được viết như user story.
- Definition of Done tồn tại.
- DoD có ít nhất 4 detailed completion checks.
- DoD phù hợp story type.
- Không lẫn domain không liên quan.

### 8.4 Evaluator xử lý non-ready status

Nếu Planner trả:

```text
NEEDS_CLARIFICATION
```

Evaluator không yêu cầu AC/task/DoD như story READY. Thay vào đó nó kiểm tra:

- có ít nhất 3 clarification questions.
- không có ready-story fields.
- trả REVISION để chặn Jira.

Nếu Planner trả:

```text
SPLIT_RECOMMENDED / NEEDS_SPLIT
```

Evaluator kiểm tra:

- có story_splits.
- có sprint_allocation.
- trả REVISION để chặn Jira parent ticket.

Nếu Planner trả:

```text
REVISION
```

Evaluator coi đây là trạng thái hợp lệ nhưng chưa Jira-ready. Nó trả REVISION và đưa warning/revision instruction rõ ràng.

### 8.5 Vì sao Evaluator không approve non-ready story?

Đây là guardrail quan trọng:

```text
Chỉ story có planning_status=READY và evaluator status=APPROVED mới được action.
```

Điều này ngăn:

- tạo Jira từ request mơ hồ.
- tạo Jira từ parent oversized request.
- tạo Jira khi Planner bị lỗi LLM/context.
- tạo Jira từ output thiếu AC/task/DoD.

---

## 9. Finalizer và Action Gate

Finalizer đảm bảo downstream action chỉ chạy khi:

```text
story.planning_status == READY
and
evaluation.status == APPROVED
```

Nếu không đạt:

```text
Action blocked until evaluator returns APPROVED and planning_status is READY.
```

Các action bị chặn:

- Jira create issue.
- Slack notification.
- GitHub branch creation.

Trong execute-all, hệ thống chạy theo thứ tự:

```text
Jira first
→ nếu Jira success thì tạo GitHub branch nếu config tồn tại
→ Slack notification kèm Jira info
```

---

## 10. Benchmark và chất lượng hiện tại

Các artifact benchmark hiện có trong repo cho thấy hệ thống đã có baseline để đánh giá:

### 10.1 LLM-as-a-judge benchmark

File:

```text
data/final_evaluation_report_v2.json
```

Kết quả trung bình trên 135 case:

- Domain & Type: 2.79 / 5.
- Feature Recognition: 2.60 / 5.
- Requirement Classification: 2.59 / 5.
- Task Scope: 2.23 / 5.

Ý nghĩa:

- Agent đã hiểu domain/type ở mức dùng được cho draft.
- Feature recognition ở mức khá cho MVP local model.
- Task scope còn là điểm cần cải thiện.

### 10.2 RAG quality report

File:

```text
src/ai_scrum_master/evaluation/rag_quality_report.json
```

Kết quả:

- hit_rate_at_k: 0.90.
- recall_at_k: 0.90.
- precision_at_k: 0.4167.
- MRR: 0.90.
- NDCG@k: 0.90.

Ý nghĩa:

- Hệ thống thường tìm được nguồn đúng trong top-k.
- Nhưng precision còn thấp, nghĩa là vẫn có context nhiễu.
- Cần cải thiện reranking/filtering để Planner ít bị kéo lệch domain.

---

## 11. Rủi ro kỹ thuật hiện tại

### 11.1 Context window của local model

Local Ollama có thể bị lỗi nếu prompt quá dài:

```text
request exceeds available context size
```

Đã có hướng xử lý:

- compact prompt.
- giảm context items.
- bỏ few-shot với context window nhỏ.
- giữ warning nếu Planner vẫn không tạo được READY story.

### 11.2 Retrieval precision còn hạn chế

RAG hit rate tốt nhưng precision thấp. Điều này có thể gây:

- Planner lấy context đúng nhưng lẫn context nhiễu.
- Output bị domain contamination.
- Task scope bị rộng hoặc sai trọng tâm.

Khuyến nghị:

- tăng chất lượng lexical rerank.
- thêm keyword extraction tốt hơn ở Analyzer.
- thêm architecture map/source map.
- lưu metadata domain/file path rõ hơn.

### 11.3 Test/lint chưa hoàn toàn sạch

Codebase hiện có một số test legacy import path chưa đồng bộ sau refactor. Trước khi rollout doanh nghiệp, cần:

- sửa test imports.
- bổ sung compatibility hoặc cập nhật test suite.
- chạy CI cho backend/frontend.
- chuẩn hóa `.env.example`.

---

## 12. Đề xuất triển khai

### Phase 0: Technical Hardening

Mục tiêu:

- Đồng bộ env/docs theo stack hiện tại: LangGraph, Qdrant, React.
- Sửa test/lint critical.
- Chuẩn hóa prompt compact cho local model.
- Thêm test cho context overflow và planner revision.
- Kiểm tra project-level retrieval isolation.

### Phase 1: Pilot nội bộ

Mục tiêu:

- Dùng với một squad hoặc một project test.
- Chỉ cho preview Jira/Slack, human approval bắt buộc.
- Đo KPI:
  - thời gian tạo draft story.
  - tỷ lệ output READY.
  - số vòng revision.
  - tỷ lệ AC/DoD hợp lệ.
  - feedback từ PM/Dev/QA.

### Phase 2: Controlled rollout

Mục tiêu:

- Mở rộng cho nhiều project.
- Bổ sung role/permission.
- Secret management tốt hơn.
- Observability cho pipeline.
- Dashboard benchmark/quality.

---

## 13. Kết luận

PM-Agent hiện đã có kiến trúc đủ rõ cho một MVP kỹ thuật nghiêm túc:

- Có ingestion và embedding local.
- Có RAG trên Qdrant.
- Có Researcher để đóng gói evidence.
- Có Planner sinh structured story.
- Có deterministic quality gate.
- Có Evaluator chặn output chưa đạt.
- Có finalizer/action gate trước Jira/Slack/GitHub.

Giá trị hiện tại phù hợp nhất là:

```text
AI-assisted backlog drafting + PM-controlled approval
```

Không nên định vị hệ thống là tự động thay thế PM/PO. Nên định vị là công cụ tăng tốc refinement, chuẩn hóa output và giảm rủi ro tạo Jira từ requirement chưa đủ rõ.

