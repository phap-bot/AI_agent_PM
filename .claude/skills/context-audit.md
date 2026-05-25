---
name: context-audit
description: Assess whether retrieved project context is sufficient, relevant, and trustworthy enough for planning.
tags: [#context, #coverage, #confidence, #retrieval-check]
slash: /context-audit
---

# Purpose
Measure context quality before story generation.

# When to use
- After retrieval
- Before planning critical stories
- When planning quality seems generic or low-confidence

# Inputs
- Retrieved snippets
- Metadata
- Request under analysis

# Outputs
- Context sufficiency summary
- Confidence level
- Missing context list
- Planning risk notes

# Rules
- Prefer explicit missing-context warnings over weak assumptions.
- Identify mismatches between retrieved context and current request.

# Example
/context-audit
Input: Check whether current retrieval is enough for Google login planning.
