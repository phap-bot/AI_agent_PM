# Acceptance Criteria — Best Practices

> Source: Atlassian — "What is acceptance criteria? Examples and best practices"

## What is Acceptance Criteria?

Acceptance criteria are predefined requirements and conditions that a product or task must meet to be marked as complete and accepted by the user.

These specific standards eliminate ambiguity by providing a clear "definition of done" for developers and quality assurance teams.

Establishing these benchmarks during the planning phase ensures that the final output aligns perfectly with customer expectations.

Document clear and measurable standards for every user story to ensure your team delivers exactly what the client requested.

Acceptance criteria fosters clear communication and helps define expectations. They outline the specific conditions a feature or user story must meet to be truly complete, and are sometimes referred as "Definition of Done."

Without clear acceptance criteria, teams risk confusion, missed goals, and wasted effort.

## Acceptance Criteria vs. User Story

Acceptance criteria and user stories are often discussed together, but they play fundamentally different roles in product development.

- **User stories** articulate the "why" and communicate the purpose and value of a feature from the user's perspective.
- **Acceptance criteria** define "what success looks like" and translate that purpose into explicit, verifiable requirements for implementation.

A well-crafted user story captures the customer need, the intended behavior, and the underlying motivation. This framing anchors backlog items in real user value and provides essential context for backlog grooming and prioritization.

For example, user stories could be:
- As a customer, I want to search for products by name so I can easily find what I'm looking for.

Acceptance criteria convert intent into clear, testable conditions that determine whether the story is done:
- The search function returns results that exactly match the entered product name.
- The search function returns results that partially match the entered product name.
- Results are displayed in a clear, organized, and user-friendly format.

Together, they ensure your team builds the right thing—and builds it right.

## Characteristics of Good Acceptance Criteria

- **Clarity and conciseness:** Write acceptance criteria in plain, unambiguous language. Keep them tight and outcome-focused.
- **Testability:** Every criterion must be objectively verifiable. Each criterion should map cleanly to one or more executable tests.
- **Outcome:** Describe the result, not the recipe. Strong criteria explain what the user should experience, not the technical steps required to build it.
- **Measurability:** Where possible, quantify expectations to create a definitive pass/fail threshold.
- **Independence:** Each criterion should stand on its own. Independent criteria simplify testing, reduce coupling, and make it easier to diagnose issues.

## Why Do You Need Acceptance Criteria?

- **Alignment and shared understanding:** Everyone—from engineering to QA to stakeholders—gets on the same page.
- **Reduced ambiguity and rework:** A clear definition of done prevents rework. Clarity upfront is always cheaper than correction later.
- **Improved testing efficiency:** Well-defined acceptance criteria hand QA a testing blueprint.
- **Enhanced project management:** Break a feature into measurable checkpoints, making progress visible and reducing risk.
- **Increased stakeholder satisfaction:** Clear acceptance criteria set realistic expectations and minimize ambiguity.

## How to Write Acceptance Criteria

1. **Start with the user story** — Refer to the user story connected to the acceptance criteria.
2. **Determine the outcomes** — Express the user experience and expected outcomes. What should the feature achieve for the user?
3. **Establish overall testability** — Ensure each criterion translates into a clear and verifiable test.
4. **Decide the measurability** — Whenever possible, quantify the criteria using measurable terms.
5. **Focus on independence** — Aim for independent criteria that you can test in isolation.
6. **Promote collaboration** — Involve the product owner, developers, and other relevant stakeholders.
7. **Review and refinement** — Revisit and refine the acceptance criteria throughout development.
8. **Provide clarity and concision** — Strive for clear and concise language everyone can understand.

## Who Should Write Acceptance Criteria?

- **Product owner:** Possesses a deep understanding of customer needs and product vision.
- **Development team:** Uses technical expertise to provide insights into feasibility and testability.
- **Scrum master (if applicable):** Facilitates the team discussion and ensures criteria adhere to best practices.

The final criteria should be a collective effort that integrates all stakeholder perspectives.

## Examples of Acceptance Criteria

### Example 1: Product Search

**User story:** As a customer, I want to search for products by name so I can quickly find the items I'm looking for.

**Acceptance criteria:**
- The system returns all products that exactly match the entered search term.
- The system returns partial matches when the user enters at least three characters.
- Search results display the product name, image, and price in a clear and organized layout.
- The search results page supports pagination, displaying a maximum of 20 results per page.
- If no results are found, the system displays a "No results found" message with helpful next steps.

### Example 2: Edit Account Information

**User story:** As a registered user, I want to edit my account information so I can keep my profile up to date.

**Acceptance criteria:**
- Users can access an Edit Profile section within their account settings.
- Users can update their first name, last name, email address, and phone number.
- The system validates required fields and displays errors for invalid or missing information.
- Clicking Save successfully updates the user's information in the system.
- After a successful update, the system displays a confirmation message.
- If the update fails, the system displays an actionable error message.

### Example 3: User Activity Reporting

**User story:** As an administrator, I want to generate activity reports to track user activity and engagement.

**Acceptance criteria:**
- The admin dashboard includes a dedicated Reports section.
- Administrators can generate reports on key user activities, including logins, product views, and purchases.
- Reports can be filtered by date range and user type.
- Administrators can export reports in at least two formats, including CSV and PDF.
- The system displays a clear error message if a report cannot be generated.

## Acceptance Criteria vs. Definition of Done

- **Acceptance criteria** focus on the specific functionalities a user story must fulfill to be complete for the end user.
- **Definition of Done** establishes a broader set of quality standards for all development work, encompassing non-functional aspects such as code quality and documentation.

## When Should You Write Acceptance Criteria?

- During **backlog refinement** sessions, where the team discusses and fleshes out user stories.
- During **sprint planning** when the team collaboratively finalizes the acceptance criteria for stories in the upcoming sprint.
- Always define acceptance criteria **before development begins** to ensure clear expectations.

## Challenges of Writing Acceptance Criteria

- Ambiguity in the criteria can lead to misinterpretation.
- Striking a balance between overly specific and too vague criteria.
- Disagreements among stakeholders on what constitutes "done."
- Temptation to cover every detail, leading to cumbersome and ineffective criteria.