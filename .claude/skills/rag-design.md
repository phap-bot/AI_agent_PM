---
name: rag-design
description: Design retrieval-augmented context flow for project-aware story planning.
tags: [#rag, #chromadb, #retrieval, #embedding]
slash: /rag-design
---

# Purpose
Define how the system should ingest, index, and retrieve internal project context before planning work.

# When to use
- When designing the Researcher agent
- When setting up ChromaDB ingestion and retrieval
- When improving context quality and retrieval coverage

# Inputs
- Source document types
- Project stack metadata
- Example requests

# Outputs
- Ingestion strategy
- Chunking rules
- Metadata schema
- Retrieval query strategy
- Fallback behavior when no context is found

# Rules
- Favor retrieval that supports planning decisions.
- Track confidence and warnings.
- Never hide missing-context risk.

# Example
/rag-design
Input: Design ChromaDB retrieval for AI Scrum Master story generation.
