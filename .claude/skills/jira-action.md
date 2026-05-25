---
name: jira-action
description: Translate approved story outputs into Jira issue and sub-task payloads with retry-aware execution logic.
tags: [#jira, #payload, #api, #issue-creation]
slash: /jira-action
---

# Purpose
Prepare or validate the action layer for Jira issue creation.

# When to use
- After story evaluation passes
- When mapping planner output into Jira fields
- When designing Jira integration behavior

# Inputs
- Approved stories
- Project issue field conventions
- Authentication and retry rules

# Outputs
- Jira story payload
- Sub-task payloads
- Retry guidance
- Error handling notes

# Rules
- Never bypass evaluation.
- Keep story and sub-task mapping explicit.
- Include failure handling for auth and partial creation.

# Example
/jira-action
Input: Convert approved stories into Jira REST payloads.
