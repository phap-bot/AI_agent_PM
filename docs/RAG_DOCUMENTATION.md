# Báo cáo Tài liệu Kỹ thuật: Hệ thống RAG (Retrieval-Augmented Generation)

Tài liệu này mô tả chi tiết về hệ thống RAG được triển khai trong **AI Scrum Master Agent**, nhằm cung cấp bối cảnh (context) dự án cho các LLM Agent để sinh ra User Story chính xác và sát thực tế nhất.

## 1. Mục Tiêu của RAG trong Hệ thống
Trong quy trình làm phần mềm, một yêu cầu (requirement) thô thường thiếu thông tin về tech stack, kiến trúc, và các quy ước của dự án. Hệ thống RAG giải quyết vấn đề này bằng cách:
- Cung cấp **Project Context** (quy ước chung, kiến trúc) và **Feature Context** (tính năng liên quan).
- Giúp Planner Agent không bị "ảo giác" (hallucinate) mà luôn dựa trên thông tin có thật trong codebase/tài liệu.
- Định hướng luồng sinh acceptance criteria đúng chuẩn dự án.

## 2. Kiến trúc & Công nghệ

### 2.1. Vector Database & Embedding Model
- **Vector Store:** **ChromaDB** được sử dụng ở chế độ local persistent (lưu trên ổ cứng tại `src/ai_scrum_master/data/chromadb/`). Nó nhẹ, nhanh và không cần setup server riêng.
- **Embedding Model:** `nomic-embed-text` thông qua nền tảng **Ollama**. Mô hình này nhỏ gọn, hỗ trợ context window tốt và đặc biệt mạnh mẽ trong việc trích xuất vector cho các đoạn văn bản kỹ thuật.

### 2.2. Luồng Ingestion (Tiền xử lý & Indexing)
Được đặt tại `src/ai_scrum_master/ingestion/ingest.py`.
1. **Đọc tài liệu:** Các file `.md`, `.txt` hoặc `.pdf` được thu thập từ `src/ai_scrum_master/data/raw_docs/`.
2. **Chunking (Cắt nhỏ):** Tài liệu được chia nhỏ thành các chunk khoảng 1000 ký tự (có overlap 200 ký tự) để đảm bảo không mất bối cảnh ở các đoạn nối.
3. **Embedding & Lưu trữ:** Các chunk được gửi tới `nomic-embed-text` để lấy vector embeddings, sau đó lưu vào collection `ai_scrum_master_context` trên ChromaDB kèm theo metadata (tên file, chunk index).

## 3. Luồng Retrieval (Truy xuất) & Researcher Agent

### 3.1. Hybrid Search
Hệ thống sử dụng phương pháp **Hybrid Search** lai kết hợp giữa:
- **Vector Search (Semantic):** Tính khoảng cách ngữ nghĩa giữa User Requirement và Chunk.
- **Lexical Search (Keyword Match):** Cộng thêm điểm thưởng (boost) nếu chunk chứa các từ khóa quan trọng hoặc có metadata thuộc các nguồn tài liệu ưu tiên (ví dụ: `auth_context.md`).
Điểm số cuối cùng được scale (min-max) về dải từ 0.0 đến 1.0.

### 3.2. Researcher Agent
- Tương tác với hệ thống RAG thông qua custom tool `ProjectContextRagTool`.
- Agent tự động phân tích yêu cầu đầu vào, viết lại (rewrite) câu truy vấn nếu cần, và gọi RAG để lấy Top `N` tài liệu.
- **Filter & Threshold:** Các kết quả được lọc qua ngưỡng (threshold = 0.6 mặc định). Chỉ các chunk có điểm >= threshold mới được giữ lại.

## 4. Kiểm định chất lượng RAG (Quality Gate)
Hệ thống được thiết kế kèm theo một công cụ đánh giá tự động (Evaluation Benchmark) tại `tests/test_rag_quality.py` và `src/ai_scrum_master/evaluation/rag_quality_check.py`.
- **Ground Truth:** Hệ thống so sánh kết quả retrieval với danh sách tài liệu mong đợi (expected sources) cho từng use-case cụ thể.
- **Metrics đo lường:**
  - **Hit Rate @ K:** Tỷ lệ có ít nhất 1 tài liệu đúng nằm trong Top K.
  - **Recall @ K:** Tỷ lệ số tài liệu đúng được tìm thấy so với tổng số tài liệu đúng.
  - **MRR (Mean Reciprocal Rank):** Đánh giá thứ hạng của tài liệu đúng đầu tiên.
  - **NDCG:** Đánh giá thứ tự xếp hạng (ranking quality) tổng thể.

## 5. Cấu hình & Tùy biến
Bạn có thể tùy chỉnh RAG thông qua biến môi trường hoặc file `.env`:
- `OLLAMA_EMBED_MODEL`: Thay đổi model nhúng (mặc định: `nomic-embed-text`).
- `RETRIEVAL_THRESHOLD`: Ngưỡng độ tin cậy để loại bỏ kết quả nhiễu (mặc định: `0.6`).
- `RETRIEVAL_EXCERPT_CHARS`: Số lượng ký tự tối đa của một chunk khi đưa vào prompt của LLM (để tránh context quá dài).

---
*Tài liệu này được tạo tự động nhằm cung cấp cái nhìn tổng quan cho đội ngũ kỹ thuật trong quá trình bảo trì và nâng cấp AI Scrum Master Agent.*
