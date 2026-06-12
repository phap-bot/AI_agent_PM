# Dàn ý Slide Báo Cáo (Phần: Data & RAG Metrics)
**Trình bày:** Phúc

---

## Slide 1: Bài toán của LLM & Tầm quan trọng của Context
- **Vấn đề:** LLM không biết dự án đang dùng công nghệ gì → viết User Story bị "ảo giác" (hallucinate).
- **Giải pháp:** Xây dựng hệ thống RAG (Retrieval-Augmented Generation).
- **Hình ảnh gợi ý:** Sơ đồ `Yêu cầu thô` → `RAG` (tìm tài liệu nội bộ) → `Planner Agent`.

## Slide 2: Kiến trúc Vector Database & Embedding
- **Vector Store:** ChromaDB chạy hoàn toàn local (bảo mật dữ liệu công ty).
- **Embedding Model:** `nomic-embed-text` qua Ollama (nhỏ gọn, hiệu năng cao).
- **Chunking:** `chunk_size=1200`, `overlap=200` (đã thử nghiệm 3 strategies, baseline tốt nhất).

## Slide 3: Thuật toán Tìm kiếm (Hybrid Search)
- **Vấn đề:** Vector Search thuần túy dễ sai khi query ngắn ("thêm login google").
- **Giải pháp Hybrid:** Semantic + Lexical/Metadata Boost + Source-Level Dedup.
- **Hình ảnh:** Chụp code `rag.py` và `researcher.py`.

## Slide 4: Kết quả Đo lường (30 Ground Truth Queries)
- Hit Rate@3: **93.33%** (28/30 queries tìm đúng tài liệu)
- Recall@3: **93.33%** 
- MRR: **93.33%** (tài liệu đúng thường nằm top 1)
- NDCG@3: **93.33%**
- Per-source: auth=100%, checkout=100%, notification=100%, sprint=71%
- **Kết luận:** RAG sẵn sàng Production, nền tảng vững cho Agents phía sau.
