---
name: build-orchestrator
description: Design the end-to-end control flow across agents, revision loops, approval gates, and external actions.
tags: [#orchestration, #crew, #workflow, #execution]
slash: /build-orchestrator
---

# Purpose
Specify the runtime coordination logic for the AI Scrum Master system.

# When to use
- During system design
- Before implementing CrewAI orchestration
- When revising retry, approval, or escalation logic

# Inputs
- Agent responsibilities
- Contracts
- Failure and retry rules

# Outputs
- Control flow
- Transition rules
- Loop conditions
- Escalation paths

# Rules
- Evaluator must gate action execution.
- Human approval stays optional but explicit.
- Retry and escalation logic must be observable.
- Orchestration design should map cleanly to CrewAI roles and tasks.
- Runtime boundaries should remain clear between FastAPI entrypoints, CrewAI orchestration, and integration tools.

# Example
/build-orchestrator
Input: Design the loop from Researcher to Jira creation with revision caps.
