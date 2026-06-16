FEW-SHOT EXAMPLES (GOLDEN DATASET):
Below are perfect examples of how to generate a READY story from a requirement and context. Use these as a style guide for formatting, granularity, and INVEST principles.

--- Example 1: Full-stack Software Feature ---
REQUIREMENT:
Title: Implement "Forgot Password" via Email Link
Description: Users should be able to request a password reset link to their email. Clicking the link allows them to set a new password. The link expires in 15 minutes.

RETRIEVED CONTEXT:
[1] source=Security Docs: "All password reset tokens must use JWT with a 15-minute expiration. Emails are sent via SendGrid."
[2] source=UI/UX Guidelines: "Forms must use the standard `<ValidationForm>` component and show inline error messages."

EXPECTED OUTPUT:
{
  "title": "Implement Forgot Password flow via email link",
  "story_type": "software_feature",
  "jira_issue_type": "Story",
  "jira_labels": ["security", "auth", "frontend"],
  "jira_linked_items": [
    {
      "relationship": "blocks",
      "issue_key": "PROJ-999"
    }
  ],
  "user_story": "As a registered user, I want to request a password reset link to my email, so that I can securely regain access to my account if I forget my password.",
  "acceptance_criteria": [
    "Given the user submits a valid email on the Forgot Password page, When the API processes the request, Then a JWT reset token is generated with a 15-minute expiration and sent via SendGrid.",
    "Given the user clicks an expired reset link, When the page loads, Then an error message is displayed and they are prompted to request a new link.",
    "Given the user submits a new valid password, When the form is submitted, Then the password is updated in the database and the token is immediately invalidated."
  ],
  "story_points": 5,
  "tasks": {
    "be": [
      "Create POST /api/auth/forgot-password endpoint to generate 15-min JWT token and trigger SendGrid email.",
      "Create POST /api/auth/reset-password endpoint to validate JWT token and hash/save the new password."
    ],
    "fe": [
      "Build 'Forgot Password' request page using <ValidationForm>.",
      "Build 'Reset Password' page to parse token from URL and handle form submission with inline errors."
    ],
    "qa": [
      "Verify email delivery and link format across different email clients.",
      "Write automated tests for expired token and invalid token scenarios.",
      "Verify that reusing a reset token after a successful password change fails."
    ]
  },
  "definition_of_done": [
    "BE endpoints are covered by unit tests (JWT expiration, token invalidation).",
    "FE forms implement <ValidationForm> and display inline errors as per UX guidelines.",
    "QA has verified the full flow (email received, link clicked, password changed) in staging.",
    "SendGrid templates are approved and deployed."
  ],
  "planning_status": "READY",
  "clarification_questions": [],
  "assumptions": [
    "Assuming the SendGrid API key and email templates are already configured in the environment."
  ],
  "story_splits": [],
  "sprint_allocation": [],
  "context_sources": [
    {
      "id": "1",
      "source": "Security Docs",
      "chunk_index": 0,
      "score": 0.95,
      "excerpt": "All password reset tokens must use JWT with a 15-minute expiration. Emails are sent via SendGrid."
    },
    {
      "id": "2",
      "source": "UI/UX Guidelines",
      "chunk_index": 0,
      "score": 0.88,
      "excerpt": "Forms must use the standard `<ValidationForm>` component and show inline error messages."
    }
  ],
  "warnings": []
}
--- End of Example 1 ---
