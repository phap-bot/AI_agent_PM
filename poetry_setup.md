# Poetry setup

```bash
poetry init --name ai-scrum-master --python "^3.11" --no-interaction
poetry add fastapi uvicorn langgraph langchain langchain-ollama langchain-qdrant qdrant-client streamlit ollama pydantic python-dotenv
poetry add --group dev pytest
```
