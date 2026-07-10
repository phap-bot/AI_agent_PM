# Technical Proposal: PM-Agent / AI Scrum Master

## 1. Tóm tắt đề tài

PM-Agent là công cụ hỗ trợ PM/PO/Scrum Master chuyển yêu cầu thô từ stakeholder thành bản nháp work item có cấu trúc, có kiểm tra chất lượng và có cơ chế chặn trước khi đồng bộ sang Jira/Slack/GitHub.
Hệ thống được triển khai theo hướng local-first AI workflow:
- Frontend: React/Vite/Tailwind.
- Backend API: FastAPI.
- Background job: Celery + Redis.
- Orchestration: LangGraph.
- LLM runtime: Ollama local.
- Vector database: Qdrant.
- Storage/config/history: MongoDB.
- Integrations: Jira, Slack, GitHub.

## 2. Mục tiêu kỹ thuật của hệ thống

Hệ thống được thiết kế để giải quyết 5 việc chính:
1. Nhận yêu cầu từ user hoặc stakeholder.
2. Tìm context liên quan từ tài liệu đã ingest.
3. Sinh user story, acceptance criteria, story points, task BE/FE/QA và definition of done.
4. Đánh giá output có đủ điều kiện sprint-ready không.
5. Chỉ cho phép action Jira/Slack/GitHub khi output đã đạt điều kiện.
Luồng chính:

## 3. Embedding và Knowledge Retrieval

### 3.1. Embedding dùng kỹ thuật?

Hệ thống dùng kỹ thuật text embedding + vector search để biến tài liệu nội bộ thành vector, sau đó tìm các đoạn tài liệu gần nghĩa với yêu cầu của user.
- Vector store là Qdrant.
- Embedding được tạo qua langchain_ollama.OllamaEmbeddings.
- Model hiện tại là bge-m3
Luồng embedding:

```text
Document:
-> Parse text -> normalize text -> split/chunk -> embed chunk bằng
OllamaEmbeddings -> upsert vào Qdrant
```

### 3.3. Tài liệu được ingest như thế nào?

Module hỗ trợ các nguồn tài liệu dạng:

- PDF.
- DOCX.
- TXT.
- Markdown.

Quá trình ingest:

- User upload tài liệu hoặc dùng raw docs có sẵn.
- Backend/Celery xử lý bất đồng bộ.
- Tài liệu được parse thành text.
- Text được chia chunk theo cấu hình:
  - `RAG_CHUNK_SIZE`.
  - `RAG_CHUNK_OVERLAP`.
  - `RAG_MARKDOWN_CHUNK_SIZE`.
  - `RAG_MARKDOWN_CHUNK_OVERLAP`.
- Mỗi chunk có metadata:
  - Source file.
  - Chunk index.
  - Document hash.
  - Chunk hash.
  - Project ID.
- Chunk được embedding vào Qdrant.

### 3.4. Cách tìm context

```text
Requirement text
-> compact query
-> search Qdrant bằng vector similarity
-> nếu bật hybrid search: rerank bằng lexical score + vector score
-> chọn top context
-> tạo evidence package cho Planner
```

## 4. Researcher Agent

### 4.1. Researcher dùng model ?

Model: Qwen2.5:3b

### 4.2. Researcher đánh giá context như thế nào?

Researcher không chỉ lấy top-k rồi gửi cho Planner Agent còn:

- Lọc match dưới threshold.
- Giữ evidence có source/domain phù hợp.
- Tạo excerpt ngắn.
- Đánh dấu retrieval status:
  - `ok`.
  - `empty`.
  - `failed`.
  - `no_relevant_context`.
- Tạo warning nếu retrieval yếu.
- Tạo `planning_brief`.

## 5. Planner Agent

### 5.1. Planner dùng model gì?

Model: Qwen3.5-4B.

Các runtime option quan trọng cần được cấu hình phù hợp với local model và giới hạn phần cứng.

### 5.2. Planner tạo user story như thế nào?

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
"story_type": "software_feature | process_improvement | oversized_request |
ambiguous_request",
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
"planning_status": "READY | NEEDS_CLARIFICATION | NEEDS_SPLIT | SPLIT_RECOMMENDED |
REVISION",
"clarification_questions": [],
"assumptions": [],
"story_splits": [],
"sprint_allocation": [],
"context_sources": [],
"warnings": []
}
```

### 5.3. Cách tạo User Story

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
Nếu không xác định được actor, behavior hoặc outcome, Planner không nên ép tạo story mà trả NEEDS_CLARIFICATION.

### 5.4. Cách tạo Acceptance Criteria

Acceptance criteria bắt buộc theo format:
Given [context],
When [action],
Then [expected result].
Với `READY` story:
- tối thiểu 3 AC.
- AC phải test được.
- AC không được là template chung chung.
- AC phải liên quan trực tiếp đến requirement hiện tại.

Ví dụ với issue "MCP servers don't appear for agenthost target":
Given MCP servers are configured as tool sources,
When the user opens the agenthost target,
Then the configured MCP servers are visible as available tools.

### 5.5. Cách tạo Definition of Done

Definition of Done không chỉ là "code done". Nó cần thể hiện điều kiện hoàn tất story.
Với READY story, DoD cần tối thiểu 4 check:
- AC đã pass.
- BE/FE implementation hoàn tất nếu có.
- QA evidence hoặc test scenario đã có.
- edge case/failure case đã được kiểm tra.
- reviewer/PM có thể xác nhận story ready.
Evaluator có chấm điểm DoD theo nhiều dimension, nên DoD quá ngắn hoặc generic sẽ bị revision.

### 5.6. Cách tạo task BE / FE / QA

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
- Task không nên quá generic như "Implement backend endpoints".
- Task phải đúng responsibility group.
Ví dụ:
BE: Inspect agenthost tool-source resolution logic for MCP server entries.
FE: Verify the agenthost target UI renders MCP server tools when returned by backend/tool registry.
QA: Add regression coverage for MCP server visibility under agenthost target configuration.

### 5.7. Story point estimation

Story points chỉ được dùng các giá trị Fibonacci:
1, 2, 3, 5, 8, 13 Planner dùng Fibonacci vì estimate trong Agile phản ánh:
- complexity.
- uncertainty.
- integration risk.
- test scope.
- coordination effort.
Nếu LLM trả story point không thuộc Fibonacci, hệ thống sẽ reset/null và để quality gate/evaluator xử lý.

### 5.8. Handling ambiguous request

Nếu request mơ hồ, Planner trả:
planning_status = NEEDS_CLARIFICATION Khi đó:
- không tạo user_story READY.
- không tạo AC.
- không story point.
- không BE/FE/QA tasks.
- trả ít nhất 3 clarification questions.
Mục tiêu: không tạo Jira ticket khi input chưa đủ rõ.

### 5.9. Handling oversized request

Nếu request quá lớn cho một sprint, Planner trả:
planning_status = SPLIT_RECOMMENDED hoặc:
planning_status = NEEDS_SPLIT Khi đó Planner phải đề xuất:
- story_splits.
- sprint_allocation.
Parent oversized request không được coi là Jira-ready story.

## 6. Evaluator Agent

### 6.1. Vai trò

Evaluator là quality gate dung model ( Qwen 3.5:4b ) cuối trước action. Nó trả:
APPROVED hoặc:
REVISION

### 6.2. Evaluator đánh giá dựa vào :

1. Rule-based validation trong code.
2. Story output từ Planner.
3. Planning status.
4. Requirement hiện tại.
5. Route/domain.
6. Retrieved context/context sources.
7. Optional LLM evaluation nếu bật.
Điểm quan trọng: rule-based validation có thể override LLM. Nếu LLM nói approved nhưng rule fail, hệ thống vẫn trả REVISION.

### 8.3. Các tiêu chí Evaluator kiểm tra với READY story

Evaluator kiểm tra:
- User story có đủ As a / I want / so that.
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

## 9. Finalizer và Action Gate

Finalizer đảm bảo downstream action chỉ chạy khi:
story.planning_status == READY and evaluation.status == APPROVED Nếu không đạt Action blocked until evaluator returns APPROVED and planning_status is READY.
Các action bị chặn:
- Jira create issue.
- Slack notification.
- GitHub branch creation.
Trong execute-all, hệ thống chạy theo thứ tự:

```text
Jira first
-> nếu Jira success thì tạo GitHub branch nếu config tồn tại
-> Slack notification kèm Jira info
```

## 10. Benchmark và chất lượng hiện tại

### 10.1. LLM-as-a-judge benchmark

Kết quả trung bình trên 135 case:
- Domain & Type: 2.79 / 5.
- Feature Recognition: 2.60 / 5.
- Requirement Classification: 2.59 / 5.
- Task Scope: 2.23 / 5.
Ý nghĩa:
- Agent đã hiểu domain/type ở mức dùng được cho draft.
- Feature recognition ở mức khá cho MVP local model.
- Task scope còn là điểm cần cải thiện.

### 10.2. PM-Agent vs OpenRouter Benchmark

Kết quả trên 135 mẫu:
- Type Accuracy: 80.00%
- Domain Accuracy: 62.96%
- Complexity Accuracy: 56.30%
- Team Accuracy: 60.74%
Chỉ số Macro F1:
- Type F1-Score: 40.31%
- Domain F1-Score: 35.34%
- Complexity F1-Score: 38.52%
- Team F1-Score: 43.85%
Ý nghĩa:
- Agent nhận diện loại yêu cầu tốt nhất, với Type Accuracy đạt 80.00%.
- Domain và Team đạt mức dùng được cho draft, nhưng vẫn cần kiểm duyệt.
- Complexity là điểm yếu , chỉ đạt 56.30% Accuracy.
- Macro F1 còn thấp, cho thấy agent vẫn khó xử lý các lớp ít dữ liệu hoặc yêu cầu mơ hồ.

### 10.2. RAG quality report

File:
src/ai_scrum_master/evaluation/rag_quality_report.json Kết quả:
- hit_rate_at_k: 0.90.
- recall_at_k: 0.90.
- precision_at_k: 0.4167.
- MRR: 0.90.
- NDCG@k: 0.90.
Ý nghĩa:
- Hệ thống thường tìm được nguồn đúng trong top-k.
- Nhưng precision còn thấp, nghĩa là vẫn có context nhiễu.
- Cần cải thiện reranking/filtering để Planner ít bị kéo lệch domain.

## 11. Kết luận

PM-Agent hiện đã có kiến trúc đủ rõ cho một MVP kỹ thuật chuẩn pipeline:
- Có ingestion và embedding local.
- Có RAG trên Qdrant.
- Có Researcher để đóng gói evidence.
- Có Planner sinh structured story.
- Có deterministic quality gate.
- Có Evaluator chặn output chưa đạt.
- Có finalizer/action gate trước Jira/Slack/GitHub.
