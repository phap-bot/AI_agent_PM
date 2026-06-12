# Báo Cáo Kỹ Thuật: Module RAG & Dữ Liệu (AI Scrum Master Agent)
**Người thực hiện:** Phúc (Data & Retrieval Lead)  
**Dự án:** AI Scrum Master Agent - Tự động hóa quy trình Sprint Planning

---

## 1. Tổng Quan Kiến Trúc RAG (Retrieval-Augmented Generation)

Trong hệ thống AI Scrum Master, để LLM (Planner Agent) có thể sinh ra User Story và cấu trúc Task chính xác, hệ thống không thể chỉ dựa vào kiến thức nền của LLM. Module RAG được xây dựng nhằm cung cấp **bối cảnh dự án (Project Context)** cho Agent.

Kiến trúc RAG được thiết kế tối ưu cho môi trường local:
- **Vector Database:** ChromaDB (Local Persistent). Dữ liệu context không bị rò rỉ ra bên ngoài, tốc độ truy xuất nhanh mà không cần deploy server riêng.
- **Embedding Model:** `nomic-embed-text` (Chạy local qua Ollama). Kích thước nhỏ nhưng hiệu năng vượt trội cho tài liệu kỹ thuật.
- **Agent Phụ Trách:** `ResearcherAgent` — tìm kiếm tài liệu dự án trước khi đưa cho Planner.

## 2. Chiến lược Ingestion & Chunking

Quá trình chuẩn bị dữ liệu (Data Ingestion) đóng vai trò sống còn đối với chất lượng RAG.
- **Nguồn dữ liệu (Corpus):** 7 files trong `raw_docs/`: `auth_context.md`, `checkout_context.md`, `notification_context.md`, `sprint_policy.md`, `scrum_guide_2020.pdf`, `acceptance_criteria.pdf`, `user_stories.pdf`.
- **Chunking Strategy:** Recursive Character Text Splitting với `chunk_size=1200`, `chunk_overlap=200`.
- **Thử nghiệm W8:** Đã so sánh 3 strategies (800/100, 1200/200, 1600/300). Baseline 1200/200 đạt composite score cao nhất (0.8378).

## 3. Quá Trình Retrieval (Hybrid Search)

Thách thức: yêu cầu đầu vào thường rất ngắn và mơ hồ. Giải pháp **Hybrid Search**:
- **Semantic Search:** Cosine similarity giữa embedding của Requirement và Chunk.
- **Lexical/Keyword Boost:** Tăng điểm cho chunks chứa metadata ưu tiên hoặc từ khóa khớp.
- **Source-Level Dedup:** Chỉ giữ best chunk mỗi source file → đa dạng hóa Top-K → cải thiện Precision.
- **Confidence Threshold:** Lọc matches có score >= 0.6.

## 4. Đo lường & Đánh Giá (RAG Metrics)

Hệ thống RAG được đánh giá qua **30 Ground Truth queries** phủ 5 domain:

| Metric | Kết quả (30 queries) | Target | Đạt? |
|--------|---------------------|--------|------|
| Hit Rate@3 | **0.9333** | >= 0.80 | ✅ |
| Recall@3 | **0.9333** | >= 0.70 | ✅ |
| Precision@3 | **0.4556** | >= 0.50 | ⚠️ |
| MRR | **0.9333** | >= 0.70 | ✅ |
| NDCG@3 | **0.9333** | >= 0.70 | ✅ |

**Per-source Recall:** auth=1.0, checkout=1.0, notification=1.0, sprint_policy=0.71.

**Error Analysis:** Q15 và Q17 miss do *Corpus Dominance* — `acceptance_criteria.pdf` lấn át `sprint_policy.md`. Đã enrich keyword và áp dụng source-level dedup nhưng 2 queries vẫn miss.

## 5. Kết luận

Module RAG đã hoạt động ổn định với 4/5 metrics vượt target. Precision@3 chưa đạt 0.50 do corpus dominance giữa PDF và MD files. Hệ thống tích hợp thành công vào Full Pipeline, cung cấp nền tảng bối cảnh vững chắc giúp Planner Agent tạo User Story mà không bị hallucination.
