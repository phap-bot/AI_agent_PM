import inspect

import ai_scrum_master.core.requirement_router as requirement_router
from ai_scrum_master.core.context_selector import select_context_for_route
from ai_scrum_master.core.pipeline import ScrumMasterCrew
from ai_scrum_master.core.requirement_router import route_requirement
from ai_scrum_master.core.story_validator import validate_post_generation


class FakeResearcher:
    def __init__(self, context: dict) -> None:
        self.context = context

    def run(self, requirement: str, n_results: int = 5, route: dict | None = None) -> dict:
        result = dict(self.context)
        result["route"] = route or {}
        return result


class FakePlanner:
    def __init__(self, story: dict) -> None:
        self.story = story
        self.context = None

    def run(self, requirement: str, context: dict, requirement_type: str | None = None, route: dict | None = None) -> dict:
        self.context = context
        story = dict(self.story)
        story.setdefault("story_type", requirement_type or "software_feature")
        story.setdefault("route", route or {})
        return story


class FakeEvaluator:
    def run(self, story: dict) -> dict:
        return {"status": "APPROVED", "issues": [], "revision_instructions": [], "dod_score": {}, "warnings": []}


class FakeTool:
    def prepare_action(self, *args, **kwargs) -> dict:
        return {"ready": True, "payload": {"summary": "ok"}, "subtasks": [], "warnings": []}


def build_crew(context: dict, story: dict) -> ScrumMasterCrew:
    crew = ScrumMasterCrew.__new__(ScrumMasterCrew)
    crew.researcher = FakeResearcher(context)
    crew.planner = FakePlanner(story)
    crew.evaluator = FakeEvaluator()
    crew.jira_tool = FakeTool()
    crew.slack_tool = FakeTool()
    crew.task_profiles = {}
    return crew


def test_router_returns_central_profile_for_domain() -> None:
    route = route_requirement(
        "As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password."
    )

    assert route["domain"] == "auth_google_login"
    assert route["profile"]["template_name"] == "auth_google_login"
    assert route["profile"]["required_sources"] == ["auth_context"]
    assert "google_oauth_success_flow" in route["profile"]["required_concepts"]


def test_router_keyword_helpers_use_central_domain_keywords() -> None:
    source = inspect.getsource(requirement_router)

    assert "DOMAIN_KEYWORDS" in source
    assert '("login", "log in", "sign in"' not in source
    assert '("slack", "webhook", "email notification"' not in source


def test_context_selector_deduplicates_same_source_chunk() -> None:
    route = route_requirement(
        "As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password."
    )
    duplicate_context = mixed_context(
        [
            source("auth-1", "auth_context.md", "JWT authentication login Google OAuth callback."),
            source("auth-1-copy", "auth_context.md", "JWT authentication login Google OAuth callback."),
        ]
    )

    selected = select_context_for_route("Google login", duplicate_context, route)

    assert len(selected["selected_context_sources"]) == 1
    assert len(selected["matches"]) == 1


def test_post_generation_validator_returns_normalized_story_contract() -> None:
    requirement = "As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password."
    route = route_requirement(requirement)
    context = select_context_for_route(
        requirement,
        mixed_context([source("auth-1", "auth_context.md", "JWT authentication Google OAuth callback.")]),
        route,
    )
    weak_story = google_login_story()
    weak_story["acceptance_criteria"] = ["Given login starts, when it works, then the user is signed in."]

    result = validate_post_generation(requirement, weak_story, context, route)

    assert result["passed"] is False
    assert result["warnings"] == []
    assert result["normalized_story"]["planning_status"] == "REVISION"
    assert weak_story["planning_status"] == "READY"


def test_google_login_routes_selects_auth_and_requires_google_concepts() -> None:
    result = build_crew(
        mixed_context(
            [
                source("auth-1", "auth_context.md", "JWT authentication login logout Google OAuth callback token refresh."),
                source("checkout-1", "checkout_context.md", "Checkout payment order inventory."),
            ]
        ),
        google_login_story(),
    ).run("As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password.")

    assert result["context"]["route"]["domain"] == "auth_google_login"
    assert [item["source"] for item in result["context"]["selected_context_sources"]] == ["auth_context.md"]
    assert result["story"]["story_type"] == "software_feature"
    assert result["evaluation"]["status"] == "APPROVED"
    assert result["actions"]["jira"]["ready"] is True


def test_checkout_retry_selects_checkout_and_blocks_wrong_domains() -> None:
    result = build_crew(
        mixed_context(
            [
                source("checkout-1", "checkout_context.md", "Checkout payment provider timeout retry duplicate order backend totals."),
                source("auth-1", "auth_context.md", "Google OAuth callback JWT token."),
            ]
        ),
        checkout_retry_story(),
    ).run("As a signed-in shopper, I want to retry checkout payment after the payment provider times out, so that I can complete my order without creating duplicate orders.")

    assert result["context"]["route"]["domain"] == "checkout_duplicate_payment"
    assert [item["source"] for item in result["context"]["selected_context_sources"]] == ["checkout_context.md"]
    assert result["evaluation"]["status"] == "APPROVED"
    assert result["actions"]["jira"]["ready"] is True


def test_sprint_planning_missing_optional_policy_warns_but_does_not_block() -> None:
    result = build_crew(
        mixed_context(
            [
                source("scrum-1", "scrum_guide_2020.pdf", "Sprint Planning defines Sprint Goal Product Backlog Sprint Backlog Definition of Done."),
            ]
        ),
        sprint_planning_story(),
    ).run("As a Scrum Master, I want to improve Sprint Planning so that the Scrum Team can define a clear Sprint Goal before selecting Product Backlog items.")

    assert result["context"]["route"]["domain"] == "sprint_planning_process"
    assert [item["source"] for item in result["context"]["selected_context_sources"]] == ["scrum_guide_2020.pdf"]
    assert result["context"]["missing_optional_sources"] == ["sprint_policy"]
    assert any("Optional context source 'sprint_policy'" in warning for warning in result["context"]["warnings"])
    assert result["story"] is not None
    assert result["evaluation"]["status"] == "APPROVED"


def test_oversized_portal_is_split_and_not_actionable() -> None:
    result = build_crew(
        mixed_context([]),
        {
            "title": "Customer Portal",
            "story_type": "oversized_request",
            "user_story": "",
            "acceptance_criteria": [],
            "story_points": None,
            "tasks": {"be": [], "fe": [], "qa": []},
            "definition_of_done": [],
            "planning_status": "SPLIT_RECOMMENDED",
            "story_splits": [
                {"title": "Authentication capability"},
                {"title": "Billing capability"},
                {"title": "Admin dashboard capability"},
                {"title": "Notifications capability"},
                {"title": "Analytics capability"},
                {"title": "Profile management capability"},
                {"title": "Reporting capability"},
            ],
            "sprint_allocation": [{"sprint": 1, "stories": ["Authentication capability"]}],
            "warnings": [],
        },
    ).run(
        "Build a full customer portal with authentication, billing, admin dashboard, notifications, analytics, profile management, and reporting.",
        allow_fallback_without_context=True,
    )

    assert result["context"]["route"]["domain"] == "oversized_request"
    assert result["story"]["planning_status"] == "SPLIT_RECOMMENDED"
    assert result["evaluation"]["status"] == "REVISION"
    assert result["actions"]["jira"]["ready"] is False
    assert {split["title"].lower().replace(" capability", "") for split in result["story"]["story_splits"]} >= {
        "authentication",
        "billing",
        "admin dashboard",
        "notifications",
        "analytics",
        "profile management",
        "reporting",
    }


def test_ambiguous_login_keeps_context_but_requests_clarification() -> None:
    result = build_crew(
        mixed_context([source("auth-1", "auth_context.md", "JWT login OAuth callback token.")]),
        {
            "title": "Improve Login",
            "story_type": "ambiguous_request",
            "user_story": "",
            "acceptance_criteria": [],
            "story_points": None,
            "tasks": {"be": [], "fe": [], "qa": []},
            "definition_of_done": [],
            "planning_status": "NEEDS_CLARIFICATION",
            "clarification_questions": [
                "Which login flow should be improved?",
                "What outcome should change?",
                "Which failure paths must be covered?",
            ],
            "warnings": [],
        },
    ).run("Improve login")

    assert result["context"]["route"]["domain"] == "ambiguous_request"
    assert result["story"]["planning_status"] == "NEEDS_CLARIFICATION"
    assert result["story"]["story_points"] is None
    assert result["story"]["tasks"] == {"be": [], "fe": [], "qa": []}
    assert len(result["story"]["clarification_questions"]) >= 3
    assert result["evaluation"]["status"] == "REVISION"
    assert result["actions"]["jira"]["ready"] is False


def mixed_context(sources: list[dict]) -> dict:
    return {
        "documents": [item["document"] for item in sources],
        "matches": sources,
        "retrieved_sources": [
            {
                "id": item["id"],
                "source": item["metadata"]["source"],
                "chunk_index": item["metadata"].get("chunk_index", 0),
                "score": item["score"],
                "excerpt": item["document"],
            }
            for item in sources
        ],
        "context_snippets": [
            f"[{index}] source={item['metadata']['source']} chunk=0 score={item['score']}: {item['document']}"
            for index, item in enumerate(sources, start=1)
        ],
        "retrieval_status": "ok" if sources else "empty",
        "warnings": [],
        "confidence": 0.9 if sources else 0.0,
        "quality_gate": {"passed": True, "failures": []},
    }


def source(identifier: str, source_name: str, document: str) -> dict:
    return {
        "id": identifier,
        "document": document,
        "metadata": {"source": source_name, "chunk_index": 0},
        "score": 0.9,
        "distance": 0.2,
    }


def google_login_story() -> dict:
    return {
        "title": "Google Sign-In for Returning Users",
        "story_type": "software_feature",
        "user_story": "As a returning user, I want to sign in with Google so that I can access my account quickly without entering a password.",
        "acceptance_criteria": [
            "Given a returning user starts Google OAuth sign-in, when the OAuth callback succeeds, then the backend exchanges the provider code server-side and creates a JWT-based API session.",
            "Given Google returns the user's email, when the backend processes the callback, then it maps the Google email to an existing user or creates a pending user record.",
            "Given Google authentication is cancelled or rejected, when the frontend receives the callback failure, then it shows a clear error and access tokens are not exposed in URL query parameters.",
        ],
        "story_points": 3,
        "tasks": {
            "be": [
                "Implement Google OAuth callback endpoint.",
                "Exchange Google provider code server-side.",
                "Map Google email to existing user or create pending user record.",
                "Create JWT-based API session.",
                "Ensure access tokens are not exposed in URL query parameters.",
            ],
            "fe": [
                "Add Sign in with Google button.",
                "Redirect to Google authentication flow.",
                "Handle successful OAuth callback.",
                "Show error when Google authentication is cancelled or rejected.",
            ],
            "qa": [
                "Test successful Google sign-in.",
                "Test cancelled or rejected authentication.",
                "Test existing user and pending user mapping.",
                "Verify access tokens are not exposed in URL query parameters.",
            ],
        },
        "definition_of_done": [
            "All acceptance criteria pass for Google OAuth callback success and failure.",
            "Backend and frontend implementation covers provider code exchange, email mapping, JWT session creation, and login UI.",
            "QA testing covers successful Google sign-in, cancelled or rejected authentication, and user mapping.",
            "Access tokens are verified as not exposed in URL query parameters.",
        ],
        "planning_status": "READY",
        "warnings": [],
    }


def checkout_retry_story() -> dict:
    return {
        "title": "Checkout Payment Retry Without Duplicate Orders",
        "story_type": "software_feature",
        "user_story": "As a signed-in shopper, I want to retry checkout payment after a provider timeout so that I can complete my order without duplicate orders.",
        "acceptance_criteria": [
            "Given a signed-in shopper is on the same checkout attempt and the payment provider times out, when the shopper retries payment, then the frontend shows a retry message and keeps the checkout attempt active.",
            "Given checkout totals are displayed for retry, when payment is retried, then the frontend uses backend-calculated final price, discount, tax, and shipping totals.",
            "Given the shopper retries payment after a provider timeout, when the backend processes the retry, then duplicate order prevention ensures only one order is created.",
        ],
        "story_points": 5,
        "tasks": {
            "be": ["Implement retry-safe checkout payment handling with backend-calculated totals and duplicate order prevention."],
            "fe": ["Show checkout retry message and backend-calculated totals for the same checkout attempt."],
            "qa": ["Validate payment timeout retry, duplicate submit protection, backend totals, and only one order created."],
        },
        "definition_of_done": [
            "All checkout retry acceptance criteria pass.",
            "Backend and frontend implementation covers timeout retry, backend totals, and duplicate order prevention.",
            "QA testing validates provider timeout retry, duplicate submit protection, and one order created.",
            "The completed checkout flow creates only one order for the retry attempt.",
        ],
        "planning_status": "READY",
        "warnings": [],
    }


def sprint_planning_story() -> dict:
    return {
        "title": "Improve Sprint Planning Around Sprint Goal",
        "story_type": "process_improvement",
        "user_story": "As a Scrum Master, I want to improve Sprint Planning so that the Scrum Team can define a clear Sprint Goal before selecting Product Backlog items.",
        "acceptance_criteria": [
            "Given Sprint Planning starts, when the Scrum Team defines the Sprint Goal, then the goal is agreed before selecting Product Backlog items.",
            "Given Product Backlog items are candidates for the Sprint, when the Scrum Team selects work, then each selected item supports the Sprint Goal.",
            "Given Sprint Planning is completed, when the Sprint Backlog is created, then it includes the Sprint Goal, selected Product Backlog items, and a delivery plan that considers team capacity and Definition of Done.",
        ],
        "story_points": 3,
        "tasks": {
            "be": ["Define Sprint Planning facilitation rules for Sprint Goal agreement and Product Backlog item selection."],
            "fe": ["Update the Sprint Planning checklist to capture Sprint Goal, selected Product Backlog items, capacity, and Definition of Done checks."],
            "qa": ["Validate the Sprint Planning process with the Scrum Team for Sprint Goal clarity and Sprint Backlog completeness."],
        },
        "definition_of_done": [
            "The Sprint Goal is agreed before selecting Product Backlog items.",
            "Selected Product Backlog items are validated as supporting the Sprint Goal.",
            "The Sprint Backlog includes the Sprint Goal, selected items, and delivery plan.",
            "Team capacity and Definition of Done are considered during Sprint Planning validation.",
        ],
        "planning_status": "READY",
        "warnings": [],
    }
