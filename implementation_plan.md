# Fast Benchmark Implementation Plan

Muc tieu cua file nay la mo ta cach chay benchmark nhanh cho pipeline planner ma khong lam thay doi runtime app.

## Muc Tieu

Hoan thanh benchmark nhieu mau trong thoi gian ngan hon bang cach giam so lan goi LLM va tan dung xu ly song song.

## Huong Thuc

### 1. Direct Context Retrieval

- Benchmark script co the bo qua cac node agent LangGraph cho rieng buoc research de query thang Qdrant bang `title` va `body` cua issue.
- Runtime app van dung LangGraph lam orchestration chinh.
- Legacy agent framework cu khong con nam trong runtime hoac benchmark path.

### 2. Prompt Collapse

- Ghep issue description va RAG context vao mot prompt duy nhat.
- Goi local LLM mot lan de sinh JSON story, acceptance criteria va tasks.

### 3. Asynchronous Pipelining

- Dung `concurrent.futures.ThreadPoolExecutor` hoac `asyncio` de day nhieu request vao hang doi Ollama.
- Can gioi han worker theo VRAM/RAM cua may chay benchmark.

## Output

- Benchmark script chinh: `data/run_fast_benchmark.py`.
- Input resume: `data/ai_planner_output.json`.
- Output can giu dung schema de co the chay tiep buoc evaluator.
