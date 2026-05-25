---
name: clarify-request
description: Detect ambiguity in incoming requests and generate the minimum clarification questions required to proceed safely.
tags: [#ambiguity, #clarification, #intake, #questioning]
slash: /clarify-request
---

# Purpose
Stop premature planning when the request lacks enough business or technical detail.

# When to use
- Vague requests
- Missing affected module or expected outcome
- Missing performance baseline or deadline context

# Inputs
- Raw request
- Any known project context

# Outputs
- Clarification questions
- Missing information categories
- Proceed recommendation: hold / partial proceed / proceed with warning

# Rules
- Ask only the minimum useful questions.
- Group questions by missing business, technical, or priority context.
- Do not generate Jira-ready stories until ambiguity is resolved.

# Example
/clarify-request
Input: The app is slow, please fix it.
