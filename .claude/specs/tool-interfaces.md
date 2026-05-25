# Tool Interfaces

## Retrieval Layer
- Input: request + metadata filters
- Output: ranked context snippets + confidence

## Planner Layer
- Input: request + retrieved context
- Output: structured story payload

## Evaluator Layer
- Input: planner payload
- Output: APPROVED or REVISION with reasons

## Jira Layer
- Input: approved story payload
- Output: created story IDs, sub-task IDs, errors

## Slack Layer
- Input: summary + Jira references
- Output: sent confirmation or error
