---
name: agent-contracts
description: Define stable input-output contracts between Researcher, Planner, Evaluator, and Action components.
tags: [#contracts, #io-schema, #handoff, #interfaces]
slash: /agent-contracts
---

# Purpose
Create machine-readable contracts so each agent can hand off work reliably.

# When to use
- During architecture design
- Before implementation of structured outputs
- When adding new agent stages

# Inputs
- Pipeline stages
- Required handoff data
- Failure and warning semantics

# Outputs
- JSON-like contracts
- Required and optional fields
- Validation expectations
- Error and warning conventions

# Rules
- Separate factual context from generated planning output.
- Include confidence and warning fields where context can be incomplete.
- Keep contracts stable across orchestration changes.

# Example
/agent-contracts
Input: Define Researcher -> Planner -> Evaluator handoff schemas.
