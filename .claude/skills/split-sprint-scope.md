---
name: split-sprint-scope
description: Decompose oversized feature requests into multiple sprint-sized user stories with suggested sequencing.
tags: [#decomposition, #scope, #epic, #sprint-planning]
slash: /split-sprint-scope
---

# Purpose
Break large requests into a realistic set of deliverable stories.

# When to use
- Large multi-capability feature requests
- Requests likely to exceed one sprint
- Feature bundles requiring phased delivery

# Inputs
- Large feature request
- Technical and sprint context

# Outputs
- List of split user stories
- Story points per story
- Total scope assessment
- Proposed sprint grouping

# Rules
- Split by capability, not arbitrary size.
- Keep each story independently valuable where possible.
- Explicitly call out cross-story dependencies.

# Example
/split-sprint-scope
Input: Build online payments with VNPay, MoMo, cards, refunds, and history.
