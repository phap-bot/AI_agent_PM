# Kịch Bản Demo: Báo cáo với Mentor (Phần của Phúc)

---

## Bước 1: Giới thiệu phần việc đảm nhận (1 phút)
**Phúc nói:** "Trong dự án AI Scrum Master Agent, em phụ trách toàn bộ luồng Data và RAG Pipeline — gồm xây dựng VectorDB, Researcher Agent, bộ đánh giá RAG Metrics, và tập 30 Ground Truth."

## Bước 2: Demo `test manual: requirement → context` (3 phút)

**Thao tác trên máy:**
```bash
.\.venv\Scripts\Activate.ps1
python scripts/test_manual_research.py -i
```

**Nhập thử:** `Thêm tính năng login bằng Google`

**Giải thích kết quả:** "Researcher Agent query vào ChromaDB bằng Hybrid Search, trả về đúng file `auth_context.md` với Confidence cao. Mặc dù câu yêu cầu rất ngắn, thuật toán vẫn tìm chính xác context phù hợp."

## Bước 3: Show mã nguồn cốt lõi (2 phút)

**Mở file:** `src/ai_scrum_master/agents/researcher.py`

**Chỉ ra:**
- Hàm `_build_retrieval_query()`: query expansion tự động
- Hàm `_top_matches()`: source-level dedup cải thiện Precision
- Hàm `_estimate_confidence()`: hệ thống tự chấm điểm tin cậy

**Nói:** "Em dùng `nomic-embed-text` chạy hoàn toàn local qua Ollama, bảo mật 100% dữ liệu công ty."

## Bước 4: Trình bày Metrics (2 phút)

**Mở file:** `src/ai_scrum_master/evaluation/rag_quality_report.json`

**Nói:** "Em xây dựng tập Ground Truth với 30 queries phủ 5 domain. Kết quả:
- Hit Rate, Recall, MRR, NDCG đều đạt **93.33%**
- Per-source recall: auth=100%, checkout=100%, notification=100%
- sprint_policy đạt 71% do corpus dominance issue đã được document rõ."

## Bước 5: Demo Full Pipeline (2 phút nếu còn thời gian)

```bash
python scripts/test_manual_pipeline.py -r "Thêm tính năng login bằng Google"
```

**Nói:** "Đây là toàn bộ pipeline chạy end-to-end: Researcher tìm context → Planner tạo User Story → Evaluator đánh giá → Action Preview cho Jira/Slack."

---
*Mẹo: Nhấn mạnh việc không chỉ "gọi API" mà còn **đo lường bằng code (30 GT Metrics)** để chứng minh tính hiệu quả.*
