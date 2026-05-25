---
name: vector-store-setup
description: Define persistent ChromaDB and Ollama embedding setup for the Researcher agent.
tags: [#chromadb, #embeddings, #vector-store, #retrieval]
slash: /vector-store-setup
---

# Purpose
Specify how `core/vector_store.py` should persist and retrieve project context locally.

# When to use
- When implementing ChromaDB persistence
- When configuring `nomic-embed-text` via Ollama
- When defining collection strategy for project docs

# Inputs
- Persistence path
- Embedding model
- Document sources
- Retrieval goals

# Outputs
- ChromaDB initialization plan
- Embedding setup pattern
- Collection and persistence guidance
- Retrieval readiness notes

# Rules
- Use persistent local storage.
- Keep embedding configuration explicit.
- Separate ingestion concerns from retrieval concerns.

# Example
/vector-store-setup
Input: Design `core/vector_store.py` for persistent ChromaDB under `data/chromadb/`.
