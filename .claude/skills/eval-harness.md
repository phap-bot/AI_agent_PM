---
name: eval-harness
description: Build the benchmark and regression structure used to test story generation quality and pipeline behavior.
tags: [#benchmark, #dataset, #regression, #testing]
slash: /eval-harness
---

# Purpose
Define how to measure whether the AI Scrum Master Agent is actually improving.

# When to use
- Before demos
- During regression testing
- When adding prompts, tools, or new agent behaviors

# Inputs
- Example requests
- Gold stories or rubric
- Dataset candidates

# Outputs
- Test set structure
- Scenario categories
- Scoring dimensions
- Regression recommendations

# Rules
- Include clear, ambiguous, oversized, and failure-path cases.
- Score both format quality and execution readiness.
- Preserve a stable benchmark core set.

# Example
/eval-harness
Input: Build a benchmark for AI Scrum Master story quality.
