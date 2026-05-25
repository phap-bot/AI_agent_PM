---
name: slack-notify
description: Prepare Slack notifications for created stories, escalation events, and team handoff moments.
tags: [#slack, #notification, #team-update, #handoff]
slash: /slack-notify
---

# Purpose
Define how the system communicates task creation and failure events to the team.

# When to use
- After Jira actions
- During escalation or retry exhaustion
- For PM and team notifications

# Inputs
- Story summary
- Jira links or identifiers
- Escalation context

# Outputs
- Slack message draft or payload
- Channel intent
- Notification rationale

# Rules
- Keep notifications concise and actionable.
- Separate success notifications from escalation alerts.
- Include assumptions when relevant.

# Example
/slack-notify
Input: Draft a message for newly created sprint stories.
