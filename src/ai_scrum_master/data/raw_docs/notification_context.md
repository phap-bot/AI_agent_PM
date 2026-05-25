# Notification Context

The system sends notifications for important workflow events.

Channels:
- Slack is used for internal team notification.
- Email is used for customer-facing notification.
- In-app notification is used for user dashboard events.

Slack usage rules:
- Scrum story notifications go to the product delivery channel.
- Messages must include title, story points, evaluation status, and Jira reference when available.
- Failed Jira creation must alert the PM instead of silently failing.

QA expectations:
- Verify notification payload content.
- Verify missing webhook configuration produces a warning.
- Verify notification is blocked when evaluator status is REVISION.
