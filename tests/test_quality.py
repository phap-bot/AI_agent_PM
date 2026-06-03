import inspect

from ai_scrum_master.agents.evaluator import EvaluatorAgent
from ai_scrum_master.agents.planner import PlannerAgent
import ai_scrum_master.core.quality as quality
from ai_scrum_master.core.quality import (
    AMBIGUOUS_REQUEST,
    OVERSIZED_REQUEST,
    PROCESS_IMPROVEMENT,
    SOFTWARE_FEATURE,
    classify_requirement,
    filter_context_sources_for_requirement,
    validate_story_against_requirement,
)
from ai_scrum_master.core.quality_gate import evaluate_research_output
from ai_scrum_master.core.story_validator import evaluate_planner_output
from ai_scrum_master.core.domain_profiles import DOMAIN_KEYWORDS, DOMAIN_SOURCE_TERMS


def test_quality_domain_rules_use_central_domain_profiles() -> None:
    source = inspect.getsource(quality)

    assert "auth" in DOMAIN_KEYWORDS
    assert "scrum" in DOMAIN_SOURCE_TERMS
    assert "DOMAIN_KEYWORDS = {" not in source
    assert "DOMAIN_TO_SOURCES = {" not in source


def test_agents_use_shared_given_when_then_validator() -> None:
    evaluator_source = inspect.getsource(EvaluatorAgent)
    planner_source = inspect.getsource(PlannerAgent)

    assert "is_given_when_then_ordered(" in evaluator_source
    assert "is_given_when_then_ordered(" in planner_source
    assert "def _is_given_when_then" not in evaluator_source
    assert "def _is_given_when_then_ordered" not in planner_source


def test_classifies_google_login_as_software_feature() -> None:
    assert classify_requirement("As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password") == SOFTWARE_FEATURE


def test_classifies_sprint_planning_as_process_improvement() -> None:
    assert classify_requirement("Create a user story for improving Sprint Planning so the Scrum Team can define a clear Sprint Goal") == PROCESS_IMPROVEMENT


def test_classifies_oversized_portal() -> None:
    assert classify_requirement("Build a full customer portal with authentication, billing, admin dashboard, notifications, analytics, profile management, and reporting") == OVERSIZED_REQUEST


def test_classifies_ambiguous_request() -> None:
    assert classify_requirement("Improve onboarding") == AMBIGUOUS_REQUEST
    assert classify_requirement("Improve login") == AMBIGUOUS_REQUEST


def test_classification_uses_only_current_requirement_keywords() -> None:
    assert classify_requirement("Add logout from authenticated routes") == SOFTWARE_FEATURE
    assert classify_requirement("Create an email alert when Jira notification delivery fails") == SOFTWARE_FEATURE
    assert classify_requirement("Facilitation improvements for Sprint Retrospective Definition of Done review") == PROCESS_IMPROVEMENT
    assert classify_requirement("Build a platform with billing and audit logs") == OVERSIZED_REQUEST


def test_oversized_classification_takes_priority_over_domain_keywords() -> None:
    assert classify_requirement("Build a full portal with authentication, billing, admin dashboard, notifications, analytics, reporting, permissions, and audit logs") == OVERSIZED_REQUEST


def test_filters_auth_context_from_mixed_retrieval() -> None:
    selected, ignored = filter_context_sources_for_requirement(
        "As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password",
        [
            {"source": "auth_context.md", "excerpt": "JWT OAuth login callback"},
            {"source": "scrum_guide_2020.pdf", "excerpt": "Sprint Planning creates a Sprint Goal"},
        ],
    )

    assert [source["source"] for source in selected] == ["auth_context.md"]
    assert [source["source"] for source in ignored] == ["scrum_guide_2020.pdf"]


def test_filters_checkout_notification_and_scrum_contexts() -> None:
    sources = [
        {"source": "auth_context.md", "excerpt": "JWT OAuth login callback"},
        {"source": "checkout_context.md", "excerpt": "Cart payment order shipping tax inventory"},
        {"source": "notification_context.md", "excerpt": "Slack email webhook alert payload"},
        {"source": "scrum_guide_2020.pdf", "excerpt": "Sprint Planning creates a Sprint Goal"},
    ]

    selected, ignored = filter_context_sources_for_requirement("Add retry payment from the checkout cart", sources)
    assert [source["source"] for source in selected] == ["checkout_context.md"]
    assert {source["source"] for source in ignored} == {"auth_context.md", "notification_context.md", "scrum_guide_2020.pdf"}

    selected, ignored = filter_context_sources_for_requirement("Send Slack email alert when notification payload delivery fails", sources)
    assert [source["source"] for source in selected] == ["notification_context.md"]
    assert {source["source"] for source in ignored} == {"auth_context.md", "checkout_context.md", "scrum_guide_2020.pdf"}

    selected, ignored = filter_context_sources_for_requirement("Improve Sprint Planning so the Scrum Team defines a Sprint Goal", sources)
    assert [source["source"] for source in selected] == ["scrum_guide_2020.pdf"]
    assert {source["source"] for source in ignored} == {"auth_context.md", "checkout_context.md", "notification_context.md"}


def test_filters_oversized_context_to_scrum_policy_and_named_domains() -> None:
    sources = [
        {"source": "auth_context.md", "excerpt": "JWT OAuth login callback"},
        {"source": "checkout_context.md", "excerpt": "Cart payment order shipping tax inventory"},
        {"source": "notification_context.md", "excerpt": "Slack email webhook alert payload"},
        {"source": "scrum_planning_policy.md", "excerpt": "Split oversized requests during Sprint Planning"},
    ]

    selected, ignored = filter_context_sources_for_requirement("Build a full portal with authentication, billing, notifications, analytics, and audit logs", sources)

    assert {source["source"] for source in selected} == {"auth_context.md", "notification_context.md", "scrum_planning_policy.md"}
    assert [source["source"] for source in ignored] == ["checkout_context.md"]


def test_validator_rejects_auth_story_with_sprint_content() -> None:
    issues = validate_story_against_requirement(
        "As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password",
        {
            "story_type": "process_improvement",
            "planning_status": "READY",
            "acceptance_criteria": [
                "Given the Sprint Goal is reviewed, when Product Backlog items are selected, then Sprint Planning is complete.",
                "Given OAuth succeeds, when callback returns, then the user is signed in.",
                "Given auth fails, when callback returns, then the user sees an error.",
            ],
            "story_points": 3,
            "tasks": {"be": ["As a Scrum Team member, I want planning"], "fe": ["Define UI or client impact"], "qa": ["Prepare validation scenarios"]},
            "definition_of_done": ["Acceptance criteria pass.", "QA validation complete.", "Sprint Goal clear.", "Product Backlog reviewed."],
        },
    )

    assert any("story_type" in issue for issue in issues)
    assert "Output contains unrelated Sprint Planning content for an authentication requirement." in issues
    assert any("not user stories" in issue for issue in issues)
    assert any("placeholder" in issue for issue in issues)


def test_validator_rejects_domain_contamination_for_general_benchmark_story() -> None:
    issues = validate_story_against_requirement(
        "'WCS.all_world2pix' failed to converge when plotting WCS with non linear distortions",
        {
            "story_type": "software_feature",
            "planning_status": "READY",
            "user_story": "As a developer, I want WCS plotting to work so that astronomical images render correctly.",
            "acceptance_criteria": [
                "Given WCS distortions exist, when plotting an image, then the grid renders without NoConvergence.",
                "Given quiet convergence handling is needed, when world coordinates are converted, then plotting continues safely.",
                "Given regression tests run, when the WCS issue is reproduced, then the expected plot behavior is verified.",
            ],
            "story_points": 3,
            "tasks": {
                "be": ["Implement Google OAuth callback handling, server-side provider-code exchange, user mapping, and JWT session issuance."],
                "fe": ["Develop WCS plotting display behavior for non-linear distortions."],
                "qa": ["Validate WCS plotting regression for NoConvergence scenarios."],
            },
            "definition_of_done": [
                "Acceptance criteria pass.",
                "Implementation is complete.",
                "QA validation is complete.",
                "NoConvergence regression is covered.",
            ],
        },
    )

    assert "Output contains unrelated auth content for a general requirement." in issues


def test_validator_requires_ordered_given_when_then() -> None:
    issues = validate_story_against_requirement(
        "As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password",
        {
            "story_type": "software_feature",
            "planning_status": "READY",
            "user_story": "As a returning user, I want to sign in with Google.",
            "acceptance_criteria": [
                "When the OAuth callback succeeds, Given the user started Google sign-in, then the backend creates a JWT session.",
                "Given Google returns the user's email, when the backend processes the callback, then it maps the email to an existing user.",
                "Given Google authentication is rejected, when the callback fails, then the frontend shows a clear error.",
            ],
            "story_points": 3,
            "tasks": {
                "be": ["Implement Google OAuth callback endpoint."],
                "fe": ["Add Sign in with Google button."],
                "qa": ["Test successful and rejected Google authentication."],
            },
            "definition_of_done": ["Acceptance criteria pass.", "QA validation complete.", "No token leakage.", "OAuth callback works."],
        },
    )

    assert "Acceptance criterion #1 must use Given / When / Then." in issues


def test_research_quality_gate_passes_when_top_result_matches_requirement_domain() -> None:
    result = evaluate_research_output(
        "As a returning user, I want to sign in with Google, so that I can access my account quickly.",
        [
            {"id": "auth-1", "metadata": {"source": "auth_context.md"}, "score": 0.91},
            {"id": "scrum-1", "metadata": {"source": "scrum_guide_2020.pdf"}, "score": 0.74},
        ],
        k=3,
    )

    assert result["passed"] is True
    assert result["metrics"]["hit_rate_at_k"] == 1.0
    assert result["metrics"]["mrr"] == 1.0


def test_research_quality_gate_fails_when_expected_source_is_missing() -> None:
    result = evaluate_research_output(
        "As a returning user, I want to sign in with Google, so that I can access my account quickly.",
        [
            {"id": "checkout-1", "metadata": {"source": "checkout_context.md"}, "score": 0.88},
            {"id": "notify-1", "metadata": {"source": "notification_context.md"}, "score": 0.82},
        ],
        k=3,
    )

    assert result["passed"] is False
    assert "authcontext" in result["expected_sources"]
    assert any("hit_rate_at_k" in failure for failure in result["failures"])


def test_planner_quality_gate_passes_grounded_ready_story() -> None:
    story = {
        "title": "Google Sign-In for Returning Users",
        "story_type": "software_feature",
        "user_story": "As a returning user, I want to sign in with Google so that I can access my account quickly.",
        "acceptance_criteria": [
            "Given Google OAuth is available on the login page, when the returning user selects Google sign-in, then the frontend starts the OAuth flow without exposing tokens in the URL.",
            "Given Google returns an authorization code to the callback, when the backend validates the callback, then it exchanges the code server-side and creates a JWT API session.",
            "Given Google authentication is cancelled or rejected, when the callback returns an error, then the frontend shows a clear sign-in failure message and does not create a session.",
        ],
        "story_points": 3,
        "tasks": {
            "be": ["Implement Google OAuth callback code exchange and JWT session creation."],
            "fe": ["Add Google sign-in entry point and callback error handling on the login page."],
            "qa": ["Validate happy-path Google login, rejected OAuth, expired token, and logout regression scenarios."],
        },
        "definition_of_done": [
            "Callback validation and token handling unit tests pass.",
            "Integration tests cover the full Google OAuth callback flow.",
            "QA validates happy-path and failure-path sign-in scenarios.",
            "No access token is exposed in URL query parameters.",
        ],
        "planning_status": "READY",
        "context_sources": [{"source": "auth_context.md"}],
    }

    result = evaluate_planner_output(
        "As a returning user, I want to sign in with Google, so that I can access my account quickly.",
        story,
        {"retrieved_sources": [{"source": "auth_context.md"}]},
    )

    assert result["passed"] is True
    assert result["metrics"]["given_when_then_ordered_count"] == 3
    assert all(result["metrics"]["task_groups_ready"].values())


def test_planner_quality_gate_fails_weak_ac_tasks_and_missing_context_citation() -> None:
    story = {
        "title": "Google Login",
        "story_type": "software_feature",
        "user_story": "As a returning user, I want Google login so that I can access my account quickly.",
        "acceptance_criteria": ["Given login starts, when Google returns."],
        "story_points": 3,
        "tasks": {"be": ["Do backend"], "fe": [], "qa": ["Test"]},
        "definition_of_done": ["Done."],
        "planning_status": "READY",
        "context_sources": [{"source": "checkout_context.md"}],
    }

    result = evaluate_planner_output(
        "As a returning user, I want to sign in with Google, so that I can access my account quickly.",
        story,
        {"retrieved_sources": [{"source": "auth_context.md"}]},
    )

    assert result["passed"] is False
    assert any("3 ordered Given/When/Then" in failure for failure in result["failures"])
    assert any("FE task" in failure for failure in result["failures"])
    assert any("Definition of Done" in failure for failure in result["failures"])


def test_planner_quality_gate_fails_near_duplicate_acceptance_criteria() -> None:
    story = {
        "title": "Checkout Payment Retry",
        "story_type": "software_feature",
        "user_story": "As an authenticated shopper, I want checkout payment retry so that duplicate orders are avoided.",
        "acceptance_criteria": [
            "Given a payment provider timeout occurs, when the shopper retries payment, then checkout shows a retry message without creating a duplicate order.",
            "Given the payment provider times out, when the shopper retries payment, then the system shows a retry message without creating a duplicate order.",
            "Given inventory mismatch occurs during checkout, when order creation is attempted, then order creation is blocked and the shopper is asked to update the cart.",
        ],
        "story_points": 3,
        "tasks": {
            "be": ["Implement retry-safe checkout payment handling with duplicate order protection."],
            "fe": ["Show retry messaging after payment provider timeout."],
            "qa": ["Validate payment timeout retry and duplicate submit protection."],
        },
        "definition_of_done": [
            "All acceptance criteria pass with validation evidence.",
            "Backend and frontend implementation is complete.",
            "QA testing covers checkout retry scenarios.",
            "No duplicate order is created after retry.",
        ],
        "planning_status": "READY",
        "context_sources": [{"source": "checkout_context.md"}],
    }

    result = evaluate_planner_output(
        "As an authenticated shopper, I want checkout payment retry to avoid duplicate orders when the payment provider times out.",
        story,
        {"retrieved_sources": [{"source": "checkout_context.md"}]},
    )

    assert result["passed"] is False
    assert result["metrics"]["acceptance_criteria_similar_pairs"] == ["1-2"]
    assert any("distinct acceptance criteria" in failure for failure in result["failures"])


def test_planner_quality_gate_fails_task_in_wrong_responsibility_group() -> None:
    story = {
        "title": "Checkout Payment Retry",
        "story_type": "software_feature",
        "user_story": "As an authenticated shopper, I want checkout payment retry so that duplicate orders are avoided.",
        "acceptance_criteria": [
            "Given payment provider timeout occurs, when the shopper retries payment, then checkout shows a retry message without creating a duplicate order.",
            "Given inventory mismatch occurs during checkout, when order creation is attempted, then order creation is blocked and the shopper is asked to update the cart.",
            "Given checkout totals are displayed, when payment is attempted, then the frontend uses totals returned by backend calculation.",
        ],
        "story_points": 3,
        "tasks": {
            "be": ["Implement backend payment retry handling with duplicate order protection."],
            "fe": ["Validate frontend behavior by testing timeout retry and duplicate orders."],
            "qa": ["Validate successful checkout, timeout retry, and duplicate submit protection."],
        },
        "definition_of_done": [
            "All acceptance criteria pass with validation evidence.",
            "Backend and frontend implementation is complete.",
            "QA testing covers checkout retry scenarios.",
            "No duplicate order is created after retry.",
        ],
        "planning_status": "READY",
        "context_sources": [{"source": "checkout_context.md"}],
    }

    result = evaluate_planner_output(
        "As an authenticated shopper, I want checkout payment retry to avoid duplicate orders when the payment provider times out.",
        story,
        {"retrieved_sources": [{"source": "checkout_context.md"}]},
    )

    assert result["passed"] is False
    assert result["metrics"]["task_groups_ready"]["fe"] is False
    assert any("FE task" in failure for failure in result["failures"])


def test_planner_quality_gate_fails_generic_google_login_tasks() -> None:
    story = {
        "title": "Sign in with Google",
        "story_type": "software_feature",
        "user_story": "As a returning user, I want to sign in with Google so that I can access my account quickly without entering a password.",
        "acceptance_criteria": [
            "Given a returning user starts Google sign-in, when the Google OAuth callback succeeds, then the backend exchanges the provider code server-side and establishes a JWT-based API session.",
            "Given Google returns an email for the authenticated account, when the backend processes the callback, then it maps the email to an existing user or creates a pending user record.",
            "Given Google authentication is cancelled or rejected, when the frontend receives the failure outcome, then it shows a clear error and does not expose access tokens in URL query parameters.",
        ],
        "story_points": 3,
        "tasks": {
            "be": ["Implement the backend logic for Google login integration"],
            "fe": ["Ensure frontend redirects and displays sign-in with Google functionality correctly"],
            "qa": ["Validate the happy path, failure paths, and edge cases"],
        },
        "definition_of_done": [
            "All acceptance criteria are validated against Google sign-in success and failure paths.",
            "Backend and frontend implementation work for Google OAuth callback and login page behavior is complete.",
            "QA evidence covers Google login happy-path, failure-path, and regression scenarios.",
            "No access token is exposed in URL query parameters.",
        ],
        "planning_status": "READY",
        "context_sources": [{"source": "auth_context.md"}],
    }

    result = evaluate_planner_output(
        "As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password.",
        story,
        {"retrieved_sources": [{"source": "auth_context.md"}]},
    )

    assert result["passed"] is False
    assert result["metrics"]["task_groups_ready"] == {"be": False, "fe": False, "qa": False}


def test_domain_contamination_ignores_internal_quality_metric_names() -> None:
    story = {
        "title": "Improve Login Process",
        "story_type": "ambiguous_request",
        "user_story": "",
        "acceptance_criteria": [],
        "story_points": None,
        "tasks": {"be": [], "fe": [], "qa": []},
        "definition_of_done": [],
        "planning_status": "NEEDS_CLARIFICATION",
        "clarification_questions": [
            "Which user role or login flow should be improved?",
            "What specific login outcome should change?",
            "Which success and failure scenarios must be covered before planning?",
        ],
        "context_sources": [{"source": "auth_context.md", "excerpt": "JWT authentication and OAuth callback endpoints."}],
        "planner_quality": {
            "metrics": {
                "given_when_then_ordered_count": 0,
                "task_groups_ready": {"be": False, "fe": False, "qa": False},
            }
        },
    }

    issues = validate_story_against_requirement("Improve login", story)

    assert "Output contains unrelated checkout content for current requirement." not in issues


def test_validator_rejects_generic_context_placeholder_content() -> None:
    issues = validate_story_against_requirement(
        "As an authenticated shopper, I want checkout payment retry to avoid duplicate orders when the payment provider times out.",
        {
            "story_type": "software_feature",
            "user_story": "As a shopper, I want payment retry so that duplicate orders are avoided.",
            "acceptance_criteria": [
                "Given a documented failure condition, when that condition occurs, then the system responds according to the retrieved context.",
                "Given payment provider timeout occurs, when the shopper retries payment, then checkout shows a retry message without creating a duplicate order.",
                "Given payment succeeds after retry, when the backend creates the order, then the order is created once.",
            ],
            "story_points": 3,
            "tasks": {
                "be": ["Implement the documented backend/API behavior needed for the requested capability."],
                "fe": ["Show retry messaging after payment provider timeout."],
                "qa": ["Test timeout retry does not duplicate orders."],
            },
            "definition_of_done": [
                "All acceptance criteria pass.",
                "Backend and frontend implementation is complete.",
                "QA validation is complete.",
                "No duplicate order is created after retry.",
            ],
            "planning_status": "READY",
        },
    )

    assert any("generic template text" in issue for issue in issues)
    assert any("generic placeholder task" in issue for issue in issues)
