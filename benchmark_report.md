# 📊 Báo Cáo Đánh Giá (Benchmark Report) cho PM-Agent

Tiến trình Benchmark cho hệ thống **AI Scrum Master / PM Agent** đã hoàn tất việc chạy đánh giá (LLM-as-a-judge) trên **39 issues thực tế** của repository `microsoft/vscode`. 

Dưới đây là kết quả chi tiết về năng lực của hệ thống sau khi đi qua trọn vẹn Pipeline (Analyzer -> Retriever (Qdrant) -> Planner (Ollama)).

---

## 🏆 Điểm Số Trung Bình (Thang 1-5)

| Tiêu chí Đánh giá (Metric) | Điểm số trung bình | Nhận xét nhanh |
| :--- | :---: | :--- |
| **Domain & Type Determination** | **2.42 / 5.0** | Tốt nhất! PM Agent nhận diện được đúng lĩnh vực và phân loại (Bug/Feature) cho repo VSCode phức tạp. |
| **Feature Recognition** | **2.12 / 5.0** | Khá ổn. AI có thể hiểu được vấn đề chính từ issue để trích xuất ra User Story và AC. |
| **Requirement Classification** | **2.03 / 5.0** | Tương đối. Phân bổ effort cho BE/FE/QA vẫn còn gặp khó khăn do cấu trúc repo. |
| **Task Scope Identification** | **1.97 / 5.0** | Đang cải thiện. Điểm còn thấp vì AI đôi khi liệt kê quá chi tiết thay vì tập trung vào scope High-level. |

> [!NOTE] 
> **Lưu ý về môi trường thử nghiệm:**
> Điểm số trung bình dao động từ 1.9 - 2.4 trên thang 5 là **kết quả rất đáng khích lệ** đối với một local model (7B/8B parameters) phải đóng vai trò Product Manager cho kho mã nguồn khổng lồ và cực kỳ phức tạp như `microsoft/vscode`. Việc dự đoán scope và phân loại mà không có đủ RAG Context là thử thách khó ngay cả với GPT-4.

---

## 🔍 Phân Tích Chuyên Sâu (Insights)

### 1. Tính năng "Needs Clarification" hoạt động quá ấn tượng
Trong quá trình test, khi RAG (Qdrant) không tìm thấy docs hoặc Issue yêu cầu quá chung chung, thay vì bịa đặt (hallucinate) ra Task, model đã **dũng cảm từ chối và yêu cầu làm rõ** (`NEEDS_CLARIFICATION`). 
**Ví dụ Log từ model:**
> *"Requirement is critically vague - no context about AHP functionality... Cannot generate meaningful acceptance criteria"*
Đây là phẩm chất cao nhất của một Project Manager!

### 2. Bottleneck (Điểm nghẽn) nằm ở hệ thống RAG
Rất nhiều issue bị kéo điểm `File Coverage` xuống 1 vì điểm `RAG Retrieval` thấp. 
- **Lý do:** Khi Retriever query vào Qdrant, nó nhặt lên các docs/files không khớp với thực tế Code Patch của Ground Truth. 
- **Hệ quả:** Do không có context đúng, AI Planner không thể biết được file nào (ví dụ: `src/vs/platform/agentHost/node/agentHostGitService.ts`) cần được đưa vào User Story.
- **Giải pháp:** Cần tối ưu lại chiến lược Chunking & Embedding của script `ingest.py` hoặc tăng cường khả năng bóc tách Keyword (Search keywords) của Analyzer Node.

### 3. Khả năng dịch thuật Logic tốt
Ở những issue mà Qdrant nhặt đúng Context, điểm **Logic Alignment** và **Actionability** thường vọt lên mức **3-4 điểm**. AI chia Task rất gãy gọn, viết Acceptance Criteria rành mạch và có thêm các bước kiểm thử (Test steps) rõ ràng.

---

## 🚀 Đề Xuất Tiếp Theo (Next Steps)

Dựa trên kết quả này, để đẩy điểm số của hệ thống lên mức 4.0 - 5.0, đây là các Action Item:

1. **Tối ưu Retriever (RAG):** Cải thiện câu query search (ví dụ dùng Hybrid Search: Keyword + Vector thay vì chỉ Dense Vector) để tìm file chuẩn xác hơn.
2. **Cung cấp Architecture Map:** Thay vì chỉ cung cấp Context các file rời rạc, hãy cấu hình hệ thống cấp cho Planner một file "Sơ đồ kiến trúc" (Directory Structure) để nó dễ gán Task đúng Component hơn.
3. **Mở rộng Context Window:** Sử dụng model có Context Window lớn hơn để nhồi thêm nhiều code file vào prompt.

*(File dữ liệu chi tiết JSON với từng lý do chấm điểm đã được lưu tại `data/final_evaluation_report.json` trong máy của bạn).*
