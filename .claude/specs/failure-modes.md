# Failure Modes

## Retrieval failure
- Symptom: empty or irrelevant context
- Response: continue with warning and explicit assumptions

## Story quality failure
- Symptom: evaluator returns REVISION
- Response: send revision instructions back to planner

## Revision cap reached
- Symptom: 3 consecutive revisions
- Response: escalate to PM

## Jira auth failure
- Symptom: 401 from Jira API
- Response: refresh token and retry up to 3 times

## Notification failure
- Symptom: Slack delivery error
- Response: log failure and notify operator path
