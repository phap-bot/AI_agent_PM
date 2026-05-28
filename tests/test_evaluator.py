from ai_scrum_master.agents.evaluator import EvaluatorAgent


class FakeLLM:
    def __init__(self, output: str) -> None:
        self.output = output
        self.messages = []

    def call(self, messages: list[dict[str, str]]) -> str:
        self.messages = messages
        return self.output


class BrokenLLM:
    def call(self, prompt: str) -> str:
        raise RuntimeError("ollama unavailable")


VALID_STORY = {
    "title": "Google Login",
    "user_story": "As a user, I want Google login so that I can sign in faster.",
    "acceptance_criteria": [
        "Given Google auth is enabled, when a user clicks login, then Google OAuth starts.",
        "Given Google authentication succeeds, when the callback returns, then the user is signed in.",
        "Given authentication fails, when the provider rejects the request, then the user sees an error message.",
    ],
    "story_points": 3,
    "tasks": {
        "be": ["Implement OAuth callback and session handoff"],
        "fe": ["Add Google login button and error state"],
        "qa": ["Validate happy path and failed authentication scenarios"],
    },
    "definition_of_done": [
        "All acceptance criteria pass with clear Given/When/Then validation evidence.",
        "BE and FE implementation tasks are complete, reviewed, and integrated without known blockers.",
        "QA scenarios cover happy path, failure path, edge cases, and relevant regression checks.",
        "Story is reviewed, demo-ready, and ready for Jira creation only after evaluator approval.",
    ],
}


def test_evaluator_approves_valid_story_without_llm() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    result = evaluator.run(VALID_STORY)

    assert result["status"] == "APPROVED"
    assert result["issues"] == []


def test_evaluator_rejects_given_when_then_substrings() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = dict(VALID_STORY)
    story["acceptance_criteria"] = [
        "Given the user cancels authentication, when the frontend displays an error message.",
        "Given OAuth succeeds, when callback returns, then the user is signed in.",
        "Given OAuth fails, when callback returns, then the user sees an error.",
    ]

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert "Acceptance criterion #1 must use Given / When / Then." in result["issues"]


def test_evaluator_revises_split_recommended_before_jira_creation() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = dict(VALID_STORY)
    story["planning_status"] = "SPLIT_RECOMMENDED"
    story["story_splits"] = [{"title": "Foundation and access"}]
    story["sprint_allocation"] = [{"sprint": 1, "stories": ["Foundation and access"]}]

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert "Oversized requests must be split into sprint-ready stories before Jira creation." in result["issues"]


def test_evaluator_revises_shallow_definition_of_done() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = dict(VALID_STORY)
    story["definition_of_done"] = ["AC pass"]

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert any("Definition of done" in issue for issue in result["issues"])



def test_evaluator_revises_empty_task_groups() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = dict(VALID_STORY)
    story["tasks"] = {"be": [], "fe": ["Add button"], "qa": ["Test flow"]}

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert "Tasks must include at least one actionable BE item." in result["issues"]



def test_evaluator_requests_revision_for_invalid_story_without_llm() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    result = evaluator.run(
        {
            "title": "Bad Story",
            "user_story": "Need login",
            "acceptance_criteria": ["Only one criterion"],
            "story_points": 4,
            "tasks": {},
        }
    )

    assert result["status"] == "REVISION"
    assert len(result["issues"]) >= 3


def test_evaluator_parses_llm_json_output() -> None:
    evaluator = EvaluatorAgent(
        llm=FakeLLM(
            """
            {
              "status": "APPROVED",
              "issues": [],
              "revision_instructions": [],
              "warnings": ["Looks ready"]
            }
            """
        )
    )

    result = evaluator.run(VALID_STORY)

    assert len(evaluator.llm.messages) == 2
    assert [message["role"] for message in evaluator.llm.messages] == ["system", "user"]
    assert result["status"] == "APPROVED"
    assert result["warnings"] == ["Looks ready"]


def test_evaluator_rule_revision_overrides_llm_approval() -> None:
    evaluator = EvaluatorAgent(
        llm=FakeLLM(
            """
            {
              "status": "APPROVED",
              "issues": [],
              "revision_instructions": [],
              "warnings": []
            }
            """
        )
    )

    result = evaluator.run(
        {
            "title": "Bad Story",
            "user_story": "Need login",
            "acceptance_criteria": ["Only one criterion"],
            "story_points": 4,
            "tasks": {},
        }
    )

    assert result["status"] == "REVISION"
    assert result["issues"]


def test_evaluator_falls_back_when_llm_fails() -> None:
    evaluator = EvaluatorAgent(llm=BrokenLLM())
    result = evaluator.run(VALID_STORY)

    assert result["status"] == "APPROVED"
    assert any("Evaluator LLM unavailable" in warning for warning in result["warnings"])


def test_evaluator_rejects_auth_story_contaminated_with_sprint_planning() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {
        **VALID_STORY,
        "acceptance_criteria": [
            "Given Google auth is enabled, when a user clicks login, then Google OAuth starts.",
            "Given OAuth succeeds, when callback returns, then the user is signed in.",
            "Given the Sprint Goal is reviewed, when Product Backlog items are selected, then Sprint Planning is complete.",
        ],
    }

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert "Output contains unrelated Sprint Planning content for an authentication requirement." in result["issues"]


def test_evaluator_rejects_sprint_story_contaminated_with_auth() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {
        **VALID_STORY,
        "title": "Improve Sprint Planning",
        "requirement": "Create a user story for improving Sprint Planning so the Scrum Team can define a clear Sprint Goal and select Product Backlog items for the Sprint.",
        "story_type": "process_improvement",
        "user_story": "As a Scrum Team member, I want clearer Sprint Planning so that we can agree on a Sprint Goal and select focused Product Backlog items.",
        "acceptance_criteria": [
            "Given the Scrum Team has reviewed the Product Backlog, when Sprint Planning is completed, then the team has agreed on one clear Sprint Goal.",
            "Given Product Backlog items are candidates, when the Scrum Team selects work, then each selected item supports the Sprint Goal.",
            "Given Google OAuth returns a JWT token, when the login page handles token storage, then the user is authenticated.",
        ],
        "tasks": {
            "be": ["Define Sprint Planning inputs and Product Backlog readiness criteria"],
            "fe": ["Create Sprint Goal drafting template for the Scrum Team"],
            "qa": ["Run validation session with Scrum Team using the updated checklist"],
        },
        "definition_of_done": [
            "The Sprint Goal is clearly defined, visible, and agreed by the Scrum Team before Sprint Planning closes.",
            "Selected Product Backlog items are reviewed against the Sprint Goal and understood by the Scrum Team.",
            "The Sprint Planning facilitation checklist or template is adopted for the next planning session.",
            "The Scrum Team validates the updated planning approach and records feedback for follow-up improvement.",
        ],
    }

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert "Output contains unrelated authentication content for a Sprint Planning requirement." in result["issues"]


def test_evaluator_rejects_checkout_story_contaminated_with_scrum_and_oauth() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {
        **VALID_STORY,
        "title": "Checkout Retry Payment",
        "requirement": "As a shopper, I want to retry payment from checkout so that I can complete my order.",
        "story_type": "software_feature",
        "user_story": "As a shopper, I want to retry payment from checkout so that I can complete my order.",
        "acceptance_criteria": [
            "Given payment fails during checkout, when I retry payment, then the order can be completed.",
            "Given the cart has shipping and tax, when payment is retried, then totals stay unchanged.",
            "Given the Sprint Goal is reviewed, when Google OAuth starts, then Product Backlog items are selected.",
        ],
        "tasks": {"be": ["Implement retry payment handling"], "fe": ["Add checkout retry state"], "qa": ["Test failed and retried payment"]},
        "definition_of_done": [
            "All acceptance criteria pass with clear checkout validation evidence.",
            "BE and FE implementation tasks are complete for retry payment.",
            "QA scenarios cover failed payment, retry payment, and checkout regression checks.",
            "Story is reviewed and ready for Jira creation only after evaluator approval.",
        ],
    }

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert "Output contains unrelated Sprint Planning content for a checkout requirement." in result["issues"]
    assert "Output contains unrelated authentication content for a checkout requirement." in result["issues"]


def test_evaluator_rejects_notification_story_contaminated_with_checkout_auth_and_scrum() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {
        **VALID_STORY,
        "title": "Slack Evaluation Notification",
        "requirement": "Send a Slack alert when evaluation status changes so the team sees the Jira reference.",
        "story_type": "software_feature",
        "user_story": "As a product manager, I want a Slack alert when evaluation status changes so that the team sees the Jira reference.",
        "acceptance_criteria": [
            "Given evaluation status changes, when a Jira reference exists, then a Slack alert payload is sent.",
            "Given webhook delivery fails, when the notification is retried, then the failure is visible.",
            "Given checkout payment uses Google OAuth during Sprint Planning, when Product Backlog items are selected, then the alert is sent.",
        ],
        "tasks": {"be": ["Build notification payload sender"], "fe": ["Show notification delivery status"], "qa": ["Test Slack webhook alert delivery"]},
        "definition_of_done": [
            "All acceptance criteria pass with notification validation evidence.",
            "BE and FE implementation tasks are complete for Slack alert delivery.",
            "QA scenarios cover webhook success and failure path validation.",
            "Story is reviewed and ready for Jira creation only after evaluator approval.",
        ],
    }

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert "Output contains unrelated checkout content for a notification requirement." in result["issues"]
    assert "Output contains unrelated authentication content for a notification requirement." in result["issues"]
    assert "Output contains unrelated Sprint Planning content for a notification requirement." in result["issues"]


def test_evaluator_rejects_generic_acceptance_criteria() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {
        **VALID_STORY,
        "acceptance_criteria": [
            "Given the requirement is approved, when planning starts, then the story is documented clearly.",
            "Given Google authentication succeeds, when the callback returns, then the user is signed in.",
            "Given authentication fails, when the provider rejects the request, then the user sees an error message.",
        ],
    }

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert any("generic template" in issue for issue in result["issues"])


def test_evaluator_rejects_placeholder_tasks() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {
        **VALID_STORY,
        "tasks": {
            "be": ["Define backend changes"],
            "fe": ["Define UI or client impact"],
            "qa": ["Prepare validation scenarios"],
        },
    }

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert any("placeholder" in issue for issue in result["issues"])
    assert "Tasks must include at least one actionable BE item." in result["issues"]


def test_evaluator_rejects_user_story_shaped_tasks() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {
        **VALID_STORY,
        "tasks": {
            "be": ["As a Scrum Team member, I want to participate in Sprint Planning sessions."],
            "fe": ["Create Sprint Goal drafting template"],
            "qa": ["Run validation session with Scrum Team"],
        },
    }

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert any("not user stories" in issue for issue in result["issues"])


def test_evaluator_rejects_software_template_dod_for_process_story() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {
        **VALID_STORY,
        "story_type": "process_improvement",
        "definition_of_done": [
            "All acceptance criteria pass with clear Given/When/Then validation evidence.",
            "BE and FE implementation tasks are complete, reviewed, and integrated without known blockers.",
            "QA scenarios cover happy path, failure path, edge cases, and relevant regression checks.",
            "Story is reviewed, demo-ready, and ready for Jira creation only after evaluator approval.",
        ],
    }

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert any("software delivery template" in issue for issue in result["issues"])


def test_evaluator_approves_process_improvement_story() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {
        **VALID_STORY,
        "title": "Improve Sprint Planning",
        "story_type": "process_improvement",
        "user_story": "As a Scrum Team member, I want clearer Sprint Planning so that we can agree on a Sprint Goal and select focused Product Backlog items.",
        "acceptance_criteria": [
            "Given the Scrum Team has reviewed the Product Goal and current Product Backlog, when Sprint Planning is completed, then the team has agreed on one clear Sprint Goal.",
            "Given Product Backlog items are candidates for the Sprint, when the Scrum Team selects work, then each selected item supports the Sprint Goal and is understood by the team.",
            "Given the Sprint Planning session is complete, when the team reviews the outcome, then the Sprint Goal, selected Product Backlog items, and initial delivery plan are visible to all Scrum Team members.",
        ],
        "tasks": {
            "be": ["Define Sprint Planning inputs and Product Backlog readiness criteria"],
            "fe": ["Create Sprint Goal drafting template for the Scrum Team"],
            "qa": ["Run validation session with Scrum Team using the updated checklist"],
        },
        "definition_of_done": [
            "The Sprint Goal is clearly defined, visible, and agreed by the Scrum Team before Sprint Planning closes.",
            "Selected Product Backlog items are reviewed against the Sprint Goal and understood by the Scrum Team.",
            "The Sprint Planning facilitation checklist or template is adopted for the next planning session.",
            "The Scrum Team validates the updated planning approach and records feedback for follow-up improvement.",
        ],
    }

    result = evaluator.run(story)

    assert result["status"] == "APPROVED"


def test_evaluator_revises_clarification_needed_story() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {
        **VALID_STORY,
        "planning_status": "NEEDS_CLARIFICATION",
        "clarification_questions": ["Which users need this?"],
    }

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert any("clarification" in issue.lower() for issue in result["issues"])


def test_evaluator_does_not_require_ready_fields_for_clarification_output() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {
        "title": "Clarify login improvement request",
        "requirement": "Improve login",
        "story_type": "ambiguous_request",
        "user_story": "",
        "acceptance_criteria": [],
        "story_points": None,
        "tasks": {"be": [], "fe": [], "qa": []},
        "definition_of_done": [],
        "planning_status": "NEEDS_CLARIFICATION",
        "clarification_questions": [
            "Which user or role is affected by the login improvement?",
            "What login behavior or outcome should change?",
            "Which constraints, success criteria, or failure cases should be covered before planning?",
        ],
    }

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert result["issues"] == ["Requirement needs clarification before Jira-ready planning."]
    assert result["dod_score"] == {}


def test_evaluator_does_not_call_llm_for_non_ready_story() -> None:
    evaluator = EvaluatorAgent(
        llm=FakeLLM(
            """
            {
              "status": "REVISION",
              "issues": ["LLM noise"],
              "revision_instructions": ["LLM noise"],
              "warnings": ["LLM noise"]
            }
            """
        )
    )
    story = {
        "title": "Clarify login improvement request",
        "requirement": "Improve login",
        "story_type": "ambiguous_request",
        "user_story": "",
        "acceptance_criteria": [],
        "story_points": None,
        "tasks": {"be": [], "fe": [], "qa": []},
        "definition_of_done": [],
        "planning_status": "NEEDS_CLARIFICATION",
        "clarification_questions": [
            "Which user or role is affected by the login improvement?",
            "What login behavior or outcome should change?",
            "Which constraints, success criteria, or failure cases should be covered before planning?",
        ],
    }

    result = evaluator.run(story)

    assert evaluator.llm.messages == []
    assert result["issues"] == ["Requirement needs clarification before Jira-ready planning."]


def test_evaluator_revises_oversized_story_without_split_details() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {
        **VALID_STORY,
        "requirement": "Build a full portal with authentication, billing, admin dashboard, notifications, analytics, reporting, permissions, and audit logs.",
        "story_type": "oversized_request",
        "planning_status": "SPLIT_RECOMMENDED",
    }

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert any("story_splits" in issue for issue in result["issues"])
    assert any("sprint_allocation" in issue for issue in result["issues"])
    assert "Oversized requests must be split into sprint-ready stories before Jira creation." in result["issues"]


def test_evaluator_revises_oversized_story_marked_ready() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {
        **VALID_STORY,
        "requirement": "Build a full portal with authentication, billing, admin dashboard, notifications, analytics, reporting, permissions, and audit logs.",
        "story_type": "oversized_request",
        "planning_status": "READY",
        "story_splits": [],
    }

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert "Oversized requests must use NEEDS_SPLIT or SPLIT_RECOMMENDED planning_status." in result["issues"]
    assert "Oversized requests must include story_splits." in result["issues"]


def test_evaluator_revises_needs_split_parent_even_with_split_details() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {
        **VALID_STORY,
        "requirement": "Build a full portal with authentication, billing, admin dashboard, notifications, analytics, reporting, permissions, and audit logs.",
        "story_type": "oversized_request",
        "planning_status": "NEEDS_SPLIT",
        "story_splits": [{"title": "Portal authentication"}],
        "sprint_allocation": [{"sprint": 1, "stories": ["Portal authentication"]}],
    }

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert "Oversized requests must be split into sprint-ready stories before Jira creation." in result["issues"]


def test_evaluator_revises_ambiguous_story_without_enough_questions() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {
        **VALID_STORY,
        "requirement": "Improve onboarding",
        "story_type": "ambiguous_request",
        "planning_status": "NEEDS_CLARIFICATION",
        "clarification_questions": ["Which users need this?"],
    }

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert "Ambiguous requests must include at least 3 clarification questions." in result["issues"]


def test_evaluator_revises_ambiguous_story_marked_ready() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {
        **VALID_STORY,
        "requirement": "Improve onboarding",
        "story_type": "ambiguous_request",
        "planning_status": "READY",
        "clarification_questions": [],
    }

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert "Ambiguous requests must use NEEDS_CLARIFICATION planning_status." in result["issues"]
    assert "Ambiguous requests must include at least 3 clarification questions." in result["issues"]
class StaticEvaluatorLLM:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def call(self, messages):
        return self.payload


def test_evaluator_ignores_llm_only_false_positive_when_rules_approve() -> None:
    story = {
        "title": "Sign in with Google for Returning Users",
        "requirement": "As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password.",
        "story_type": "software_feature",
        "user_story": "As a returning user, I want to sign in with Google so that I can access my account quickly without entering a password.",
        "acceptance_criteria": [
            "Given a returning user starts Google sign-in, when the Google OAuth callback succeeds, then the backend exchanges the provider code server-side and establishes a JWT-based API session.",
            "Given Google returns an email for the authenticated account, when the backend processes the callback, then it maps the email to an existing user or creates a pending user record.",
            "Given Google authentication is cancelled or rejected, when the frontend receives the failure outcome, then it shows a clear error and does not expose access tokens in URL query parameters.",
        ],
        "story_points": 3,
        "tasks": {
            "be": ["Implement Google OAuth callback handling, server-side provider-code exchange, user mapping, and JWT session issuance."],
            "fe": ["Add Google sign-in flow handling on the login page, including callback success and cancelled/rejected error states."],
            "qa": ["Validate Google login happy path, cancelled/rejected failure path, token handling, callback validation, and protected-route regression scenarios."],
        },
        "definition_of_done": [
            "All acceptance criteria are validated against Google sign-in success and failure paths.",
            "Backend and frontend implementation work for Google OAuth callback and login page behavior is complete.",
            "QA evidence covers Google login happy-path, failure-path, and regression scenarios.",
            "No access token is exposed in URL query parameters.",
        ],
        "planning_status": "READY",
    }
    evaluator = EvaluatorAgent(
        llm=StaticEvaluatorLLM(
            {
                "status": "REVISION",
                "issues": ["Output contains unrelated checkout content for current requirement."],
                "revision_instructions": ["Output contains unrelated checkout content for current requirement."],
                "warnings": [],
            }
        )
    )

    result = evaluator.run(story)

    assert result["status"] == "APPROVED"
    assert result["issues"] == []
    assert any("ignored" in warning.lower() for warning in result["warnings"])
