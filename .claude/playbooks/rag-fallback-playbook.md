# RAG Fallback Playbook

Use when retrieval returns weak, empty, or mismatched context.

## Steps
1. Mark confidence as reduced.
2. Continue only with explicit assumptions.
3. Avoid project-specific certainty that is not supported by retrieved evidence.
4. Recommend human review when the request is high impact.
