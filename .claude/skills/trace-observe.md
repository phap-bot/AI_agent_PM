---
name: trace-observe
description: Define tracing, latency, and observability requirements for the multi-agent pipeline.
tags: [#langfuse, #tracing, #latency, #observability]
slash: /trace-observe
---

# Purpose
Make the pipeline inspectable across reasoning, retrieval, revision, and action stages.

# When to use
- When setting up Langfuse or equivalent tracing
- When diagnosing latency or failure bottlenecks
- Before demo hardening

# Inputs
- Pipeline stages
- Tool invocations
- Failure and retry events

# Outputs
- Trace map
- Required metrics
- Logging checkpoints
- Latency and failure dimensions

# Rules
- Trace every transition between agents.
- Record retries and revision counts.
- Separate model latency from integration latency.

# Example
/trace-observe
Input: Define observability for the AI Scrum Master pipeline.
