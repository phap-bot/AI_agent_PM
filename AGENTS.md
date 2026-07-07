# Project Mission
Build an AI Scrum Master Agent that converts raw stakeholder requests into validated, sprint-ready Jira work items with optional human approval and team notification.

# Implementation Stack
- Agent framework: CrewAI
- Backend API: FastAPI
- Demo UI: Streamlit
- LLM runtime: local Ollama on default port 11434
- Reasoning model: deepseek-r1:7b
- Embedding model: nomic-embed-text
- Vector store: persistent local ChromaDB
- Testing: pytest
- Hardware constraint: NVIDIA RTX 3050 4GB VRAM, so Ollama setup must prefer quantized models, modest context windows, and conservative runtime defaults to avoid OOM.

# Canonical Pipeline
Input -> Researcher -> Planner -> Evaluator -> Human Approval -> Jira/Slack Action

# Non-Negotiable Rules
- Never create Jira issues before evaluation passes.
- If a request is ambiguous, generate clarification questions before planning stories.
- If scope is too large for one sprint, split into multiple user stories and propose sprint allocation.
- If retrieval fails, continue with warnings and explicit assumptions instead of fabricated certainty.
- Revision loop is capped at 3 rounds before escalation.
- Separate task breakdown into BE / FE / QA.
- Story points must use Fibonacci values: 1, 2, 3, 5, 8, 13.

# Output Standards
- Every story must follow: As a / I want / So that.
- Every story must contain at least 3 acceptance criteria in Given / When / Then format.
- Every story must include definition of done.
- Planner outputs should be machine-readable when possible.
- Evaluator must return either APPROVED or REVISION.

# Failure Handling
- Jira 401 -> refresh auth and retry up to 3 times -> alert PM if still failing.
- Evaluator returns REVISION 3 consecutive times -> escalate to PM.
- ChromaDB returns no useful context -> proceed with reduced confidence and warning.

# Working Modes
- Use discovery mode when the goal is to extract pipeline, actors, tools, and failure modes from documents.
- Use architecture mode when the goal is to define agent responsibilities, contracts, orchestration, and concrete module boundaries across `api/`, `agents/`, `core/`, `ui/`, and `evaluation/`.
- Use MVP build mode when the goal is to implement the happy path before adding reliability layers.
- Use evaluation mode to benchmark clear, ambiguous, oversized, and failure-path requests.
- Use setup mode when the goal is to scaffold the repo, define Poetry dependencies, and configure local Ollama + ChromaDB safely for constrained VRAM.

# Slash Commands
Use the specialized skills in `.Codex/skills/` through the slash-style conventions documented in each skill file.

# Priority Scenarios
1. Clear request -> write story, AC, SP, tasks.
2. Ambiguous request -> ask clarification questions first.
3. Oversized request -> split into multiple stories and sprints.
4. Retrieval failure -> continue with explicit warning.
5. Integration failure -> retry and escalate via playbook.
