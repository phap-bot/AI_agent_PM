# Sprint Planning Policy

Stories must be sprint-ready before Jira creation.

Story quality rules:
- User story must follow: As a / I want / So that.
- Acceptance criteria must use Given / When / Then format.
- Each story must have at least 3 acceptance criteria.
- Story points must use Fibonacci values: 1, 2, 3, 5, 8, 13.
- Tasks must be split into BE, FE, and QA.

Writing acceptance criteria with Given / When / Then:
- Given describes the starting context or precondition.
- When describes the user action or system event.
- Then describes the expected outcome or system response.
- Each criterion must be independently testable.
- Use Given / When / Then to write clear, unambiguous acceptance criteria for user stories.

Oversized requirement splitting rules:
- A story estimated over 13 points is too large and must be split into smaller stories.
- Oversized requirements should be broken into multiple user stories across multiple sprints.
- Each split story must be independently deliverable and independently testable.
- Large stakeholder requests should become multiple stories across multiple sprints.
- When a requirement is oversized, the AI Scrum Master should recommend splitting into sub-stories.

Sprint sizing rules:
- Ambiguous requirements should generate clarification questions before story planning.
- Stories must be refined until all acceptance criteria are clear and testable.

Approval rules:
- Jira issues must not be created before evaluator status is APPROVED.
- If evaluation returns REVISION, the story must be revised before action preview.
