# Sprint Planning Policy

Stories must be sprint-ready before Jira creation.

## Story Quality Rules
- User story must follow: As a / I want / So that.
- Acceptance criteria must use Given / When / Then format.
- Each story must have at least 3 acceptance criteria.
- Story points must use Fibonacci values: 1, 2, 3, 5, 8, 13.
- Tasks must be split into BE, FE, and QA.

## Writing User Story with Acceptance Criteria (Given / When / Then)

When writing a user story, the team must write acceptance criteria using the Given / When / Then format:
- **Given** describes the starting context or precondition.
- **When** describes the user action or system event.
- **Then** describes the expected outcome or system response.
- Each criterion must be independently testable.
- Use Given / When / Then to write clear, unambiguous acceptance criteria for every user story.
- A well-written user story with acceptance criteria ensures the Definition of Done is explicit and verifiable.

Example acceptance criteria for a user story:
- Given a logged-in user, When they click "Add to Cart", Then the item appears in their shopping cart.
- Given a guest user, When they attempt checkout, Then the system prompts for login or registration.

## Splitting Oversized Requirements into Multiple User Stories

- A story estimated over 13 points is too large and must be split into smaller stories.
- Split oversized requirements into multiple user stories across multiple sprints.
- Each split story must be independently deliverable and independently testable.
- Large stakeholder requests should become multiple stories across multiple sprints.
- When a requirement is oversized, the AI Scrum Master should recommend splitting into sub-stories.
- Splitting ensures each user story fits within a single sprint and can be estimated accurately.

## Sprint Sizing Rules
- Ambiguous requirements should generate clarification questions before story planning.
- Stories must be refined until all acceptance criteria are clear and testable.

## Approval Rules
- Jira issues must not be created before evaluator status is APPROVED.
- If evaluation returns REVISION, the story must be revised before action preview.
