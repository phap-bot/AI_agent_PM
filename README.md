# 🚀 AI Scrum Master Agent

> **Hệ Thống Quản Lý Sản Phẩm Tự Động Hóa (Next-Generation Product Management System)**

**AI Scrum Master Agent** là một hệ thống đa tác tử (Multi-Agent) thông minh, được thiết kế để giải quyết điểm nghẽn lớn nhất trong quy trình Agile: Chuyển đổi các yêu cầu thô (raw requirements) từ các bên liên quan thành các Jira work items chi tiết, sẵn sàng cho Sprint (sprint-ready).

Bằng việc kết hợp kiến trúc **Bất đồng bộ (Asynchronous)** cấp doanh nghiệp và các mô hình **Local LLM (Ollama)**, hệ thống không chỉ tối ưu hóa hiệu suất làm việc mà còn đảm bảo bảo mật dữ liệu tuyệt đối (Zero Data Leakage).

---

## 🌟 Tổng Quan Giải Pháp & Giá Trị Cốt Lõi

- **Bảo Mật Tối Đa:** Vận hành 100% nội bộ (On-premise/Local) thông qua Ollama. Không có bất kỳ dữ liệu dự án nào bị gửi ra các API bên ngoài.
- **Kiến Trúc Multi-Agent Chuyên Sâu:** Sử dụng LangGraph để điều phối các AI Agents (Researcher, Planner, Evaluator) hoạt động độc lập và tự kiểm tra chéo, đảm bảo đầu ra đạt chuẩn.
- **Hiệu Năng & Khả Năng Mở Rộng:** Xử lý các tác vụ AI nặng dưới nền (Background Tasks) thông qua Celery và Redis, giúp giao diện (UI) luôn phản hồi mượt mà ngay cả khi có nhiều yêu cầu cùng lúc.
- **Mô Hình AI Chuyên Biệt:** Tích hợp mô hình `pm_planner_7b` đã được huấn luyện riêng biệt (Fine-tuned) trên bộ dữ liệu chuẩn mực của Product Manager.

---

## 🏗️ Kiến Trúc Hệ Thống (Architecture)

Hệ thống hoạt động theo một quy trình tự động khép kín (Pipeline):

```text
[ Yêu cầu từ Stakeholder ] 
       │
       ▼
[ FastAPI Gateway ] ──► [ Redis Message Queue ] ──► [ Celery Background Worker ]
                                                             │
                                                             ▼
                                                ╔═════════════════════════════╗
                                                ║ 🧠 Multi-Agent Orchestrator ║
                                                ║  1. Researcher Agent        ║
                                                ║  2. Planner Agent           ║
                                                ║  3. Evaluator Agent         ║
                                                ╚═════════════════════════════╝
                                                             │
       ┌─────────────────────────────────────────────────────┘
       ▼
[ Phê duyệt từ con người ] ──► [ Tích hợp tự động Jira / Slack ]
```

### 🛠️ Technology Stack
- **AI & Orchestration:** LangGraph, Ollama, Qwen 2.5 Coder (7B)
- **Backend API:** FastAPI (Python 3.10+)
- **Frontend UI:** React (Vite)
- **Background Tasks:** Celery + Redis (Message Broker & Result Backend)
- **Database (Lịch sử):** MongoDB
- **Vector Database (RAG):** Qdrant
- **Deployment:** Docker & Docker Compose

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy (Deployment Guide)

Hệ thống đã được Docker hóa hoàn toàn, mang lại trải nghiệm cài đặt "Plug-and-Play". Bạn không cần cấu hình thủ công Database hay Redis trên máy chủ.

### 1. Yêu Cầu Hệ Thống (Prerequisites)
- Đã cài đặt **Docker** và **Docker Compose**.
- Đã cài đặt **Ollama** trên máy chủ (Host machine).
- **Phần cứng khuyến nghị:** RAM tối thiểu 16GB, GPU có VRAM ≥ 8GB (để chạy mượt mà các mô hình 7B).

### 2. Khởi Tạo Mô Hình AI (Ollama)

Mở Terminal trên máy Host và tải các mô hình cơ sở:
```bash
ollama pull qwen2.5-coder:7b
ollama pull qwen-embed
```

**Cài đặt mô hình Planner (đã Fine-tune):**
Mô hình `pm_planner_7b` là "linh hồn" của hệ thống.
1. Lấy file `.gguf` (được tạo ra từ pipeline Fine-tune trên Colab/Kaggle).
2. Đặt file `.gguf` vào thư mục `src/Models/`.
3. Mở Terminal tại thư mục `src/Models/` và chạy lệnh sau để đăng ký mô hình vào Ollama:
   ```bash
   ollama create pm_planner_7b -f Modelfile.txt
   ```

### 3. Cấu Hình Biến Môi Trường (Environment Variables)

Nhân bản file cấu hình mẫu và thiết lập các thông số dự án:
```bash
cp src/ai_scrum_master/.env.example src/ai_scrum_master/.env
```

**Các biến quan trọng cần lưu ý trong file `.env`:**
```env
# Cấu hình kết nối Ollama trên máy Host
OLLAMA_BASE_URL=http://host.docker.internal:11434

# Cấu hình Mô hình phân nhiệm
OLLAMA_REASONING_MODEL=pm_planner_7b
OLLAMA_RESEARCHER_MODEL=qwen2.5-coder:7b
OLLAMA_EMBED_MODEL=qwen-embed

# Cấu hình Tích hợp (Tùy chọn)
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_PROJECT_KEY=SCRUM
JIRA_API_TOKEN=your_jira_api_token
```

### 4. Khởi Động Hệ Thống

Tại thư mục gốc của dự án, chạy lệnh sau để khởi động toàn bộ cụm dịch vụ (Microservices):
```bash
docker-compose up -d
```

Lệnh này sẽ tự động khởi tạo 6 Containers:
1. 🌐 **`api_local`**: API Gateway & Backend (Cổng `8000`)
2. 💻 **`ui_local`**: Giao diện người dùng (Cổng `5173`)
3. ⚙️ **`worker_local`**: Celery Worker (Xử lý AI bất đồng bộ)
4. 🗄️ **`mongodb_local`**: Lưu trữ dữ liệu hệ thống (Cổng `27017`)
5. 🧠 **`qdrant_local`**: Vector DB cho RAG (Cổng `6333`)
6. 📨 **`redis_local`**: Message Queue (Cổng `6379`)

**Điểm Truy Cập (Endpoints):**
- **Giao diện Người dùng:** [http://localhost:5173](http://localhost:5173)
- **Tài liệu API (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 👨‍💻 Quy Trình Phát Triển (Developer Workflow)

Hệ thống hỗ trợ **Hot-Reload thông qua Docker Volumes**, giúp tăng tốc quá trình phát triển (Development) mà không cần build lại liên tục.

- **Sửa API (FastAPI) hoặc UI (React):** Mã nguồn sẽ tự động cập nhật ngay khi bạn lưu file (`Ctrl+S`). KHÔNG cần khởi động lại container.
- **Sửa Logic AI (Celery Worker):** Do đặc thù của Celery nạp code vào bộ nhớ, mỗi khi bạn thay đổi luồng LangGraph hoặc code của Worker, hãy nạp lại cấu hình bằng lệnh:
  ```bash
  docker-compose restart worker
  ```
- **Chỉ sử dụng cờ `--build`** khi có sự thay đổi về thư viện hệ thống (`requirements.txt` hoặc `package.json`).

---

## 🩺 Cẩm Nang Khắc Phục Sự Cố (Troubleshooting)

| Hiện Tượng / Lỗi | Nguyên Nhân Cốt Lõi | Cách Khắc Phục |
| :--- | :--- | :--- |
| **`pm_planner_7b does not support tools`** | Mô hình tự custom không hỗ trợ Tool Calling. (Trong khi Agent Researcher bắt buộc phải dùng công cụ). | Kiểm tra lại `.env` đảm bảo `OLLAMA_RESEARCHER_MODEL=qwen2.5-coder:7b`. Sau đó chạy `docker-compose restart worker`. |
| **Hệ thống tải rất lâu khi "Generate"** | (Đây không phải là lỗi). Tác vụ phân tích AI đang chạy dưới nền (Background). Thời gian phụ thuộc 100% vào tốc độ của GPU. | Theo dõi tiến độ suy luận thực tế (Brainwaves) của AI thông qua log: `docker-compose logs -f worker` |
| **Lỗi bộ nhớ / Unable to allocate CPU buffer (OOM)** | Máy Host không đủ RAM hoặc Card đồ họa bị tràn VRAM. | 1. Đảm bảo bạn chỉ tải các mô hình định dạng 4-bit (`q4_k_m`).<br>2. Giảm ngữ cảnh tối đa bằng cách chỉnh `OLLAMA_NUM_CTX` trong `.env` xuống mức `2048` hoặc `4096`. |

---
*Powered by AI Multi-Agent Architecture • Built for Agile Excellence*
