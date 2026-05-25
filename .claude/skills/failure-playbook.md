---
name: failure-playbook
description: Standardize fallback, retry, and escalation behavior for retrieval, evaluation, and integration failures.
tags: [#fallback, #retry, #escalation, #resilience]
slash: /failure-playbook
---

# Purpose
Provide a consistent failure-response layer across the full pipeline.

# When to use
- During reliability planning
- When defining recovery behavior
- When triaging failed runs

# Inputs
- Failure scenario
- Current pipeline stage
- Existing retry and escalation constraints

# Outputs
- Recovery steps
- Retry decision
- Escalation path
- Operator notes

# Rules
- Prefer safe degradation over silent failure.
- Escalate after capped retry or capped revision loops.
- Preserve context for human takeover.

# Example
/failure-playbook
Input: Define what happens after 3 evaluator revisions or Jira auth failures.
