---
name: story-write
description: Convert raw stakeholder requests into sprint-ready user stories with acceptance criteria, story points, and task breakdown.
tags: [#user-story, #acceptance-criteria, #story-points, #task-breakdown]
slash: /story-write
---

# Purpose
Generate one or more implementation-ready user stories from a request.

# When to use
- When the request is sufficiently clear
- After context retrieval is available
- Before evaluator review

# Inputs
- Raw request
- Retrieved project context
- Constraints, sprint info, and assumptions

# Outputs
- Story title
- User story in As a / I want / So that format
- Minimum 3 acceptance criteria per story in Given / When / Then format
- Fibonacci story points
- BE / FE / QA task breakdown
- Definition of done

# Rules
- Do not fabricate project-specific technical decisions without context.
- If the request is too ambiguous, hand off to /clarify-request.
- If the scope is too large, hand off to /split-sprint-scope.

# Example
/story-write
Input: Add Google login before next week's demo.
