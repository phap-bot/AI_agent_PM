![](Output.001.png)AI Scrum Master Agent Đề tài Thực tập sinh![](Output.002.png)

**Created with an evaluation copy of Aspose.Words. To remove all limitations, you can use Free Temporary License [**https://products.aspose.com/words/temporary-license/**](https://products.aspose.com/words/temporary-license/)**

**ĐỀ TÀI THỰC TẬP**

**AI SCRUM MASTER AGENT**

*Tự động hóa quy trình Sprint Planning*



|**Lĩnh vực** |AI Agent / NLP / Agile Tooling |
| - | - |
|**Số thực tập sinh** |2 người |
|**Thời gian** |10 tuần |
|**Tech Stack** |Python · CrewAI · ChromaDB · Jira API |
|**Cấp độ** |Intermediate |

Phiên bản 1.0  •  2026![ref1]

1. **Tổng quan đề tài ![ref2]**
1. **Bài toán thực tế** 

Trong một team phần mềm làm Agile, mỗi sprint bắt đầu bằng việc biến yêu cầu từ khách hàng thành task cụ thể cho developer. Công việc này hiện do Scrum Master hoặc PM thực hiện thủ công theo quy trình sau: 

`  `Khách gửi email mơ hồ![](Output.005.png)

- PM đọc, hỏi lại để làm rõ
- PM viết User Story theo đúng format
- PM ước tính Story Points
- PM tạo task trên Jira, assign cho đúng người
- PM thông báo team trên Slack
- Lặp lại cho 5–15 yêu cầu mỗi sprint

Con số thực tế cho thấy quy trình này tốn kém và dễ xảy ra sai sót: 

- Mỗi sprint: 2–4 giờ chỉ để xử lý yêu cầu đầu vào 
- Dễ thiếu sót khi khối lượng lớn: quên AC, story points sai, task bị miss 
- PM mất thời gian làm việc lặp lại thay vì tập trung vào quyết định chiến lược 
2. **Tại sao các giải pháp hiện tại chưa đủ?** 



|**Giải pháp cũ**|**Làm được**|**Vẫn thiếu**|
| - | - | - |
|Template Jira / Confluence|Chuẩn hóa format|Vẫn phải điền tay, không hiểu yêu cầu|
|NLP Classifier|Phân loại loại yêu cầu|Không viết được User Story hoàn chỉnh|
|Text Summarizer|Tóm tắt email dài|Không tạo AC, không chia task|
|Rule-based bot|Tạo task theo template cố định|Vỡ khi yêu cầu không theo mẫu|
|LLM đơn thuần (ChatGPT)|Viết được User Story|Không biết stack dự án, không kết nối Jira|

3. **Giải pháp đề xuất: AI Scrum Master Agent Mục tiêu cốt lõi** ![](Output.006.png)

   là hệ thống multi-agent tự động hóa toàn bộ quy trình từ yêu cầu thô đến task trên Jira trong vòng dưới 60 giây, thay vì 30–60 phút làm tay.

Điểm khác biệt so với LLM đơn thuần: 

`  `LLM đơn thuần:  Email → [LLM] → User Story![](Output.007.png)

`  `Hạn chế: không biết stack, viết chung chung, không tạo Jira issue![](Output.008.png)

`  `(Agent):  Email → [Researcher: tra RAG] → [Planner: viết US]

- [Evaluator: kiểm tra] → [Jira] → [Slack]

`  `Ưu điểm: biết tech stack, tự kiểm tra chất lượng, tự hành động![ref1]

2. **Lý do cần AI Agent ![ref2]**

Có 5 lý do bắt buộc phải dùng Agent architecture thay vì chỉ gọi LLM đơn thuần: **Lý do 1 Truy xuất thông tin nội bộ (Tool Use)** 

Email "Thêm login Google" không chứa đủ thông tin. cần biết dự án đang dùng JWT hay session, Node.js hay Django, để viết task BE chính xác. Researcher agent tra ChromaDB để lấy context thực tế của dự án trước khi Planner viết. 

**Lý do 2 Tự kiểm tra và sửa (Self-Correction Loop)** 

Planner viết xong → Evaluator phát hiện thiếu AC cho edge case → tự yêu cầu Planner viết lại → loop tối đa 3 lần. LLM 1 lần gọi không tự làm được điều này. 

**Lý do 3 Thực hiện hành động thật (Action)** 

Sau khi viết xong, agent gọi Jira REST API tạo issue và gọi Slack Webhook gửi message. LLM chỉ sinh text, không tự gọi API. 

**Lý do 4 Xử lý yêu cầu mơ hồ (Reasoning)** 

Email "App bị chậm, fix đi" không đủ thông tin để viết US. nhận ra sự mơ hồ và chủ động hỏi lại: tính năng nào bị chậm, baseline hiện tại bao nhiêu ms, đã có APM chưa. 

**Lý do 5 Phân chia yêu cầu lớn (Planning)** 

"Làm toàn bộ module thanh toán VNPay, Momo, thẻ quốc tế" là một yêu cầu quá lớn cho 1 sprint. Planner agent chia thành 4–5 US riêng và đề xuất phân bổ sang 2 sprint. ![ref1]

3. **Kiến trúc giải pháp ![ref2]**
1. **Sơ đồ tổng thể** 

![](Output.009.jpeg)

2. **Tech Stack ![ref1]**



|**Thành phần**|**Công nghệ**|**Lý do chọn**|
| - | - | - |
|LLM reasoning|deepseek-r1:7b / Ollama|Chạy local, miễn phí, reasoning tốt|
|Embedding|nomic-embed-text|Nhỏ gọn, accuracy tốt cho tiếng Anh|
|Vector store|ChromaDB|Đơn giản, chạy local không cần server|
|Agent framework|CrewAI|API đơn giản, phù hợp multi-agent|
|UI demo|Streamlit|Nhanh, không cần frontend knowledge|
|Monitoring|Langfuse self-hosted|Xem được token, latency, trace từng bước|

4. **Flow xử lý chi tiết ![ref2]**

Toàn bộ pipeline gồm 6 bước từ input đến action: **Bước 1 Nhận yêu cầu** 

Nguồn vào: Email / Slack message / Form nhập tay. Ví dụ: "Thêm login Google, cần xong trước demo tuần sau" 

**Bước 2 Researcher Agent tra context** 

Query ChromaDB để tìm stack dự án, các US tương tự đã làm, sprint hiện tại. Trả về context đầy đủ cho Planner. 

**Bước 3 Planner Agent viết User Story** 

- Phân rã thành 1–N User Stories (mỗi US 1 chức năng rõ) 
- Viết AC theo Given/When/Then (tối thiểu 3 AC/US) 
- Ước tính Story Points theo Fibonacci: 1, 2, 3, 5, 8, 13 
- Tạo task list chia BE/FE/QA + thời gian ước tính 

**Bước 4 Evaluator Agent kiểm tra chất lượng** 

- As a / I want / So that đầy đủ? 
- Mỗi AC có Given/When/Then? 
- Story Points hợp lý với task estimate? 
- Task BE/FE/QA không bị chồng chéo? 
- Definition of Done được đề cập? 

Kết quả: APPROVED → tiếp tục / REVISION → quay lại bước 3 (tối đa 3 lần). 

**Bước 5 Human Approval (optional, 30 giây)** 

PM xem qua trên UI → bấm Approve hoặc Edit nhỏ trước khi đẩy lên Jira. 

**Bước 6 Action Layer** 

- Gọi Jira REST API → tạo Issues (Story + Sub-tasks) 
- Gọi Slack Webhook → thông báo cho team 

**4.1  Xử lý lỗi** 

- Jira API lỗi 401 → refresh token → retry tối đa 3 lần → alert PM 
- Evaluator trả REVISION 3 lần liên tiếp → escalate lên PM thủ công 
- ChromaDB không tìm được context → tiếp tục với context rỗng + warning ![ref1]
5. **Ví dụ Input / Output ![ref2]**
1. **Yêu cầu đơn giản, rõ ràng** 

Input: "Cần thêm chức năng export danh sách user ra file Excel." 

`  `USER STORY #1![](Output.010.png)

`  `─────────────────────────────────────────

`  `Title: Export User List to Excel

`  `Priority: Medium | Story Points: 3 | Sprint: Next Sprint

`  `As an admin, I want to export the user list to Excel,   so that I can analyze and  user data offline.

`  `Acceptance Criteria:

✓ Given admin clicks 'Export Excel'

`    `When the system generates the file

`    `Then a .xlsx file is downloaded within 5 seconds

`  `Tasks:

`    `[BE-001] Add GET /api/users/export endpoint 3h     [BE-002] Implement xlsx generation 2h

`    `[FE-001] Add 'Export Excel' button 1h

`    `[QA-001] Test with 100/1000/10000 rows 2h

2. **Yêu cầu mơ hồ (hỏi lại)** \
   Input: "App bị chậm, fix giúp." 

⚠️ **yêu cầu làm rõ** ![](Output.011.png)

1\. "Chậm" ở màn hình / tính năng nào? 2. Chậm bao nhiêu giây? Benchmark hiện tại? 3. Đã có APM / profiling chưa hay chỉ là cảm nhận user?

3. **Yêu cầu lớn (chia nhiều US)** 

Input: "Làm tính năng thanh toán online: VNPay, Momo, thẻ quốc tế, hoàn tiền, lịch sử giao dịch." 

- Phát hiện 5 User Stories riêng biệt:![](Output.012.png)

`  `USER STORY #1 VNPay Integration        (SP: 8)   USER STORY #2 MoMo Integration         (SP: 5)   USER STORY #3 International Card       (SP: 8)   USER STORY #4 Refund Flow              (SP: 5)

`  `USER STORY #5 Transaction History      (SP: 3)

`  `Tổng: 29 Story Points → Đề xuất chia 2 sprint   Sprint 12: US#1, US#2, US#5

`  `Sprint 13: US#3, US#4![ref1]

**6. Datasets & Tài nguyên ![ref2]**

1. **Datasets để test** 



|**Dataset![](Output.013.png)**|**Link**|**Mục đích**|
| - | - | - |
|SWE-bench|huggingface.co/datasets/princeto n-nlp/SWE-bench|Yêu cầu kỹ thuật từ GitHub Issues thật (lấy 50 mẫu đầu)|
|Jira Issues|huggingface.co/datasets/nvdimc huk/jira-issues-dataset|Issues thật từ project mã nguồn mở (100 mẫu)|
|Agile US|github.com/cscorley/changeset- feature-location|Commit message + issue → viết thành US (30 mẫu)|

2. **Repos tham khảo ![ref1]**



|**Repo**|**Mục đích**|**Điểm cần chú ý**|
| - | - | - |
|github.com/joaomdmoura/crew AI|Framework chính dùng trong dự án|Đọc kỹ phần Task, Agent, Crew|
|github.com/joaomdmoura/crew AI-examples|Ví dụ thực tế với CrewAI|Xem folder trip\_planner, ![](Output.014.png)stock\_analysis|
|github.com/langchain- ai/langchain|RAG pipeline|Đọc phần vectorstores và retrievers|
|github.com/berriai/litellm|Switch model dễ nếu cần|Thay thế Ollama nếu chuyển lên cloud|

**Evaluation Only. Created with Aspose.Words. Copyright 2003-2026 Aspose Pty Ltd.**

Confidential Internal Use Only 7 

[ref1]: Output.003.png
[ref2]: Output.004.png
