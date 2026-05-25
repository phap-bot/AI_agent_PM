---
name: story-eval
description: Evaluate generated user stories for completeness, sprint fitness, and execution readiness.
tags: [#evaluation, #rubric, #quality-check, #revision]
slash: /story-eval
---

# Purpose
Review planner output and decide whether it is ready to proceed.

# When to use
- After /story-write
- Before human approval or Jira action
- During revision loops

# Inputs
- Story draft
- Acceptance criteria
- Story points
- Task breakdown
- Definition of done

# Outputs
- APPROVED or REVISION
- Score or confidence
- Issue list
- Revision instructions

# Rules
- Check As a / I want / So that completeness.
- Check AC structure and coverage.
- Check SP reasonableness against scope.
- Check overlap between BE / FE / QA tasks.
- Cap revision cycles at 3 before escalation.

# Example
/story-eval
Input: Evaluate this planner output for Jira readiness.
