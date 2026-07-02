# Tối ưu hoá Pipeline Benchmark (Fast Benchmark)

Nhận thấy luồng Benchmark hiện tại chạy qua LangGraph tốn quá nhiều thời gian (hơn 1 phút cho 1 mẫu do phải qua nhiều node LLM trung gian như Analyzer, Researcher), kế hoạch này sẽ áp dụng chính xác 3 gợi ý tối ưu của bạn để tạo ra một script benchmark chạy siêu tốc (`data/run_fast_benchmark.py`).

## Mục tiêu
Hoàn thành 95 mẫu còn lại trong thời gian ngắn nhất bằng cách tối giản số lần gọi LLM và tận dụng xử lý song song.

## Đề xuất thay đổi

### 1. Direct Context Retrieval (Bỏ qua LLM trung gian)
- **Hành động:** Không dùng CrewAI/LangGraph cho bước Research nữa. Thay vào đó, viết một hàm Python dùng thẳng `title` và `body` của issue để query vào Qdrant (`vector_store.py`).
- **Kết quả:** Lấy được Top 5 file code liên quan (RAG Context) chỉ trong vài mili-giây mà không tốn 1 token LLM nào.

### 2. Prompt Collapse & Self-Correction (Gộp bước)
- **Hành động:** Ghép Issue Description + RAG Context vào chung 1 System Prompt duy nhất.
- **Yêu cầu LLM:** Dùng Chain-of-Thought (CoT) để LLM (pm-agent) tự suy luận và đẻ ra thẳng cấu trúc JSON chứa User Story, AC, và Tasks trong đúng 1 lượt gọi duy nhất. Cắt giảm 100% prefill time dư thừa.

### 3. Asynchronous Pipelining (Xử lý gối đầu - ThreadPool)
- **Hành động:** Thay vì vòng lặp `for` chạy tuần tự từng issue, chúng ta sẽ dùng `concurrent.futures.ThreadPoolExecutor` (hoặc `asyncio`).
- **Cơ chế:** Bắn song song 3-5 request cùng lúc vào Ollama. Mặc dù GPU xử lý tuần tự, nhưng việc đưa vào hàng đợi giúp Ollama chạy continuous batching, tận dụng 100% công suất VRAM thay vì phải liên tục chờ Python xử lý I/O.

### Chi tiết kỹ thuật:
- **Tạo file mới:** `data/run_fast_benchmark.py`
- Sẽ đọc file `data/ai_planner_output.json` để tiếp tục Resume (bỏ qua 40 mẫu đã làm).
- File này sẽ đẩy thẳng dữ liệu output ra đúng format chuẩn để có thể chạy tiếp Bước chấm điểm (Giám khảo GPT-120B).

## User Review Required

> [!IMPORTANT]
> - Các thay đổi này sẽ chỉ áp dụng cho script Benchmark để chạy đua tốc độ. Pipeline gốc (dùng LangGraph) trong ứng dụng thật (App) tạm thời mình vẫn giữ nguyên để đảm bảo kiến trúc agent linh hoạt, hoặc bạn có muốn đập đi xây lại luôn cả Pipeline gốc theo cách này không?
> - Server Ollama của bạn chịu tải được khoảng mấy request đồng thời (nếu mình set workers=3 cho ThreadPool thì có bị tràn VRAM không)?
