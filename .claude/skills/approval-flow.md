---
name: approval-flow
description: Design the optional human approval checkpoint before pushing stories into external systems.
tags: [#human-in-loop, #approval, #review-ui, #override]
slash: /approval-flow
---

# Purpose
Specify how PM review should work before Jira creation.

# When to use
- When designing the review UI or manual gate
- When deciding which fields are editable pre-publish
- When balancing autonomy and human control

# Inputs
- Evaluated story set
- UI or operational constraints

# Outputs
- Review flow
- Editable fields list
- Approve / reject / regenerate actions
- Audit considerations

# Rules
- Make approval explicit, not implicit.
- Preserve the evaluated draft separately from edited values.
- Keep small edits lightweight.

# Example
/approval-flow
Input: Design a 30-second PM review gate before Jira push.
