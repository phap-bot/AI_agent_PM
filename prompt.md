Act as an Expert AI/Backend Engineer. I am building a production-ready "AI Scrum Master Agent" that automates the generation of Agile tasks (Jira) from user requirements. 

Please help me scaffold the project directory, initialize dependency management with Poetry, and write the basic setup files for the local LLM and Vector Database.

Here is the tech stack I am using:
- LLM: deepseek-r1:7b (running locally via Ollama) [cite: 89]
- Embedding: nomic-embed-text (running via Ollama) [cite: 89]
- Vector Store: ChromaDB [cite: 89]
- Agent Framework: CrewAI [cite: 89]
- Backend: FastAPI [cite: 89]
- Frontend Demo: Streamlit [cite: 89]
- Testing: pytest

**Important Context:** I am running this on a machine with an NVIDIA RTX 3050 GPU (4GB VRAM). The setup code for Ollama must be optimized to avoid out-of-memory errors (using quantization or appropriate context limits).

**Task 1: Generate the bash script to create this exact folder structure:**
ai_scrum_master/
├── api/
│   ├── main.py
│   ├── routers/
│   └── schemas.py
├── ui/
│   └── app.py
├── agents/
│   ├── researcher.py
│   ├── planner.py
│   ├── evaluator.py
│   ├── tools/
│   │   ├── jira_tool.py
│   │   └── slack_tool.py
│   └── crew.py
├── core/
│   ├── config.py
│   ├── llm_setup.py
│   └── vector_store.py
├── data/
│   ├── raw_docs/
│   └── chromadb/
├── tests/
│   ├── test_evaluator.py
│   └── test_planner.py
├── evaluation/
│   └── evaluate_metrics.py
└── .env

**Task 2: Provide the exact `poetry init` and `poetry add` terminal commands to install the necessary dependencies for the stack mentioned above.**

**Task 3: Write the code for `core/llm_setup.py`**
- Set up the connection to the local Ollama instance (default port 11434).
- Initialize the `deepseek-r1:7b` model for CrewAI.
- Add clear comments explaining how to handle potential connection timeouts or VRAM issues.

**Task 4: Write the code for `core/vector_store.py`**
- Initialize a local persistent ChromaDB client pointing to `data/chromadb/`.
- Setup the embedding function using `nomic-embed-text` via Ollama.