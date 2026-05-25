# Jira Retry and Escalation Playbook

Use when Jira issue creation fails.

## Steps
1. Detect the failure class.
2. If 401, refresh auth and retry.
3. Retry up to 3 times for transient failures.
4. Preserve the payload and failure context.
5. Alert PM or operator after retry exhaustion.
