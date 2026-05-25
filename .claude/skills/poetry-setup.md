---
name: poetry-setup
description: Define the exact Poetry initialization and dependency installation commands for the local AI Scrum Master stack.
tags: [#poetry, #dependencies, #packaging, #bootstrap]
slash: /poetry-setup
---

# Purpose
Standardize environment setup for FastAPI, CrewAI, ChromaDB, Ollama integration, Streamlit, and pytest.

# When to use
- When initializing the Python project
- When installing production and development dependencies
- When documenting reproducible setup commands

# Inputs
- Stack definition
- Required runtime libraries
- Test and dev tool requirements

# Outputs
- Exact `poetry init` command
- Exact `poetry add` commands
- Optional dev dependency commands

# Rules
- Keep runtime and dev dependencies distinct when useful.
- Align packages with the chosen architecture.
- Prefer explicit commands over generic guidance.

# Example
/poetry-setup
Input: Generate install commands for FastAPI + CrewAI + ChromaDB + Streamlit + pytest.
