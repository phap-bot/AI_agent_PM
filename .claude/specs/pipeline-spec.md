# Pipeline Spec

Canonical flow:
1. Input intake
2. Researcher context retrieval
3. Planner story generation
4. Evaluator quality gate
5. Optional human approval
6. Jira / Slack action

Required branches:
- ambiguous request -> clarification path
- oversized request -> decomposition path
- retrieval failure -> warning path
- evaluator rejection -> revision loop
- integration failure -> retry and escalation

Implementation foundations:
- API surface should live under FastAPI modules in `api/`
- Agent logic should live under `agents/`
- Ollama runtime setup should live under `core/llm_setup.py`
- ChromaDB persistence and embeddings should live under `core/vector_store.py`
- Demo UI should live under `ui/app.py`
- Automated tests should cover planner and evaluator behavior under `tests/`
