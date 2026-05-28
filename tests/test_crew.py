from ai_scrum_master.core.finalizer import finalize_generation, should_block_planning
from ai_scrum_master.core.pipeline import ScrumMasterCrew


class FakeResearcher:
    def __init__(self, context: dict) -> None:
        self.context = context

    def run(self, requirement: str, n_results: int = 5) -> dict:
        return self.context


class FailingPlanner:
    def run(self, requirement: str, context: dict) -> dict:
        raise AssertionError("planner should not run")


class FakePlanner:
    def __init__(self, story: dict | None = None) -> None:
        self.called = False
        self.context = None
        self.story = story

    def run(self, requirement: str, context: dict, requirement_type: str | None = None) -> dict:
        self.called = True
        self.context = context
        if self.story is not None:
            return dict(self.story)
        return {
            "title": "Google Login",
            "user_story": "As a returning user, I want Google login so that I can access my account quickly.",
            "acceptance_criteria": [
                "Given Google auth is enabled, when the user starts login, then Google OAuth begins.",
                "Given OAuth succeeds, when the callback returns, then the user is signed in.",
                "Given OAuth fails, when the callback returns, then the user sees an error message.",
            ],
            "story_points": 3,
            "story_type": "software_feature",
            "tasks": {"be": ["Implement OAuth callback handling"], "fe": ["Add Google login button"], "qa": ["Test Google login success and failure"]},
            "definition_of_done": [
                "All acceptance criteria pass with clear Given/When/Then validation evidence.",
                "BE and FE implementation tasks are complete for Google login.",
                "QA scenarios cover successful login, failed login, and regression validation.",
                "Story is reviewed and ready for Jira creation only after evaluator approval.",
            ],
            "planning_status": "READY",
            "warnings": [],
        }


class FakeEvaluator:
    def run(self, story: dict) -> dict:
        return {"status": "APPROVED", "issues": [], "revision_instructions": [], "warnings": []}


class FakeTool:
    def prepare_action(self, *args, **kwargs) -> dict:
        return {"ready": True, "payload": {"summary": "would create"}, "warnings": []}


def build_crew(context: dict, planner) -> ScrumMasterCrew:
    crew = ScrumMasterCrew.__new__(ScrumMasterCrew)
    crew.researcher = FakeResearcher(context)
    crew.planner = planner
    crew.evaluator = FakeEvaluator()
    crew.jira_tool = FakeTool()
    crew.slack_tool = FakeTool()
    crew.task_profiles = {}
    return crew


def test_finalizer_blocks_approved_non_ready_story() -> None:
    result = finalize_generation(
        story={"planning_status": "NEEDS_CLARIFICATION"},
        evaluation={"status": "APPROVED", "issues": [], "revision_instructions": [], "dod_score": {}, "warnings": []},
    )

    assert result["evaluation"]["status"] == "REVISION"
    assert result["actions_ready"] is False
    assert result["actions"]["jira"]["ready"] is False
    assert "Story is not READY" in result["evaluation"]["issues"][0]


def test_finalizer_decides_when_context_blocks_planning() -> None:
    assert should_block_planning({"missing_required_sources": ["auth_context"], "retrieval_status": "ok"}, False) is True
    assert should_block_planning({"missing_required_sources": ["auth_context"], "retrieval_status": "ok"}, True) is False
    assert should_block_planning({"retrieval_status": "no_relevant_context"}, False) is True
    assert should_block_planning({"quality_gate": {"passed": False}, "retrieval_status": "ok"}, False) is True
    assert (
        should_block_planning(
            {
                "missing_optional_sources": ["sprint_policy"],
                "retrieval_status": "ok",
                "quality_gate": {"passed": True},
            },
            False,
        )
        is False
    )


def test_crew_blocks_planner_when_no_relevant_context() -> None:
    crew = build_crew(
        {
            "documents": [],
            "matches": [],
            "retrieved_sources": [],
            "retrieval_status": "no_relevant_context",
            "warnings": ["No retrieved context met relevance threshold 0.6."],
            "confidence": 0.0,
        },
        FailingPlanner(),
    )

    result = crew.run("Add Google login")

    assert result["story"] is None
    assert result["evaluation"]["status"] == "NEEDS_CONTEXT"
    assert result["actions"]["jira"]["ready"] is False
    assert result["next_steps"]


def test_crew_allows_user_approved_fallback_without_context() -> None:
    planner = FakePlanner()
    crew = build_crew(
        {
            "documents": [],
            "matches": [],
            "retrieved_sources": [],
            "retrieval_status": "empty",
            "warnings": [],
            "confidence": 0.0,
        },
        planner,
    )

    result = crew.run("Add Google login", allow_fallback_without_context=True)

    assert planner.called is True
    assert result["story"]["title"] == "Google Login"
    assert any("user-approved" in warning for warning in result["context"]["warnings"])


def test_crew_passes_only_selected_context_to_planner_and_returns_ignored_context() -> None:
    planner = FakePlanner()
    crew = build_crew(
        {
            "documents": ["Auth uses JWT and Google OAuth.", "Sprint Planning creates a Sprint Goal."],
            "context_snippets": [
                "[1] source=auth_context.md chunk=0 score=0.9: Auth uses JWT and Google OAuth.",
                "[2] source=scrum_guide_2020.pdf chunk=0 score=0.8: Sprint Planning creates a Sprint Goal.",
            ],
            "matches": [
                {"id": "auth-1", "document": "Auth uses JWT and Google OAuth.", "metadata": {"source": "auth_context.md"}, "score": 0.9},
                {"id": "scrum-1", "document": "Sprint Planning creates a Sprint Goal.", "metadata": {"source": "scrum_guide_2020.pdf"}, "score": 0.8},
            ],
            "retrieved_sources": [
                {"id": "auth-1", "source": "auth_context.md", "excerpt": "Auth uses JWT and Google OAuth.", "score": 0.9},
                {"id": "scrum-1", "source": "scrum_guide_2020.pdf", "excerpt": "Sprint Planning creates a Sprint Goal.", "score": 0.8},
            ],
            "retrieval_status": "ok",
            "warnings": [],
            "confidence": 0.9,
        },
        planner,
    )

    result = crew.run("As a returning user, I want Google login so that I can access my account quickly.")

    assert [source["source"] for source in planner.context["retrieved_sources"]] == ["auth_context.md"]
    assert planner.context["documents"] == ["Auth uses JWT and Google OAuth."]
    assert [source["source"] for source in result["context"]["selected_context_sources"]] == ["auth_context.md"]
    assert [source["source"] for source in result["context"]["ignored_context_sources"]] == ["scrum_guide_2020.pdf"]


def test_crew_post_generation_validation_blocks_contaminated_actions() -> None:
    planner = FakePlanner(
        {
            "title": "Google Sprint Planning",
            "story_type": "process_improvement",
            "user_story": "As a Scrum Team member, I want Sprint Planning so that the Sprint Goal is clear.",
            "acceptance_criteria": [
                "Given the Sprint Goal is reviewed, when Product Backlog items are selected, then Sprint Planning is complete.",
                "Given OAuth succeeds, when callback returns, then the user is signed in.",
                "Given auth fails, when callback returns, then the user sees an error.",
            ],
            "story_points": 3,
            "tasks": {"be": ["Define backend changes"], "fe": ["Define UI or client impact"], "qa": ["Prepare validation scenarios"]},
            "definition_of_done": ["Acceptance criteria pass."],
            "planning_status": "READY",
            "warnings": [],
        }
    )
    crew = build_crew(
        {
            "documents": ["Auth uses JWT and Google OAuth."],
            "retrieved_sources": [{"id": "auth-1", "source": "auth_context.md", "excerpt": "Auth uses JWT and Google OAuth.", "score": 0.9}],
            "matches": [{"id": "auth-1", "document": "Auth uses JWT and Google OAuth.", "metadata": {"source": "auth_context.md"}, "score": 0.9}],
            "retrieval_status": "ok",
            "warnings": [],
            "confidence": 0.9,
        },
        planner,
    )

    result = crew.run("As a returning user, I want Google login so that I can access my account quickly.")

    assert result["evaluation"]["status"] == "REVISION"
    assert result["story"]["planning_status"] == "REVISION"
    assert "Output contains unrelated Sprint Planning content for an authentication requirement." in result["evaluation"]["issues"]
    assert any("placeholder" in issue for issue in result["evaluation"]["issues"])
    assert result["actions"]["jira"]["ready"] is False
    assert result["actions"]["jira"]["payload"] is None
    assert result["actions"]["slack"]["ready"] is False
    assert result["actions"]["slack"]["payload"] is None


def test_crew_blocks_fallback_actions_even_when_evaluator_approves() -> None:
    planner = FakePlanner(
        {
            "title": "Google Login",
            "user_story": "As a returning user, I want Google login so that I can access my account quickly.",
            "acceptance_criteria": [
                "Given Google auth is enabled, when the user starts login, then Google OAuth begins.",
                "Given OAuth succeeds, when the callback returns, then the user is signed in.",
                "Given OAuth fails, when the callback returns, then the user sees an error message.",
            ],
            "story_points": 3,
            "story_type": "software_feature",
            "tasks": {"be": ["Implement OAuth callback handling"], "fe": ["Add Google login button"], "qa": ["Test Google login success and failure"]},
            "definition_of_done": [
                "All acceptance criteria pass with clear Given/When/Then validation evidence.",
                "BE and FE implementation tasks are complete for Google login.",
                "QA scenarios cover successful login, failed login, and regression validation.",
                "Story is reviewed and ready for Jira creation only after evaluator approval.",
            ],
            "planning_status": "READY",
            "fallback_used": True,
            "warnings": [],
        }
    )
    crew = build_crew(
        {
            "documents": ["Auth uses JWT and Google OAuth."],
            "retrieved_sources": [{"id": "auth-1", "source": "auth_context.md", "excerpt": "Auth uses JWT and Google OAuth.", "score": 0.9}],
            "matches": [{"id": "auth-1", "document": "Auth uses JWT and Google OAuth.", "metadata": {"source": "auth_context.md"}, "score": 0.9}],
            "retrieval_status": "ok",
            "warnings": [],
            "confidence": 0.9,
        },
        planner,
    )

    result = crew.run("As a returning user, I want Google login so that I can access my account quickly.")

    assert result["evaluation"]["status"] == "REVISION"
    assert any("fallback" in issue.lower() for issue in result["evaluation"]["issues"])
    assert result["actions"]["jira"]["ready"] is False
    assert result["actions"]["jira"]["payload"] is None
    assert result["actions"]["slack"]["ready"] is False
    assert result["actions"]["slack"]["payload"] is None


def test_crew_low_confidence_blocks_actions_even_when_evaluator_approves() -> None:
    planner = FakePlanner()
    crew = build_crew(
        {
            "documents": ["Auth uses JWT and Google OAuth."],
            "retrieved_sources": [{"id": "auth-1", "source": "auth_context.md", "excerpt": "Auth uses JWT and Google OAuth.", "score": 0.4}],
            "matches": [{"id": "auth-1", "document": "Auth uses JWT and Google OAuth.", "metadata": {"source": "auth_context.md"}, "score": 0.4}],
            "retrieval_status": "ok",
            "warnings": [],
            "confidence": 0.4,
        },
        planner,
    )

    result = crew.run("As a returning user, I want Google login so that I can access my account quickly.")

    assert result["evaluation"]["status"] == "REVISION"
    assert any("confidence is low" in issue.lower() for issue in result["evaluation"]["issues"])
    assert result["actions"]["jira"]["ready"] is False
    assert result["actions"]["slack"]["ready"] is False


def test_crew_post_generation_validation_sets_correct_oversized_status() -> None:
    planner = FakePlanner(
        {
            "title": "Full Portal",
            "story_type": "software_feature",
            "user_story": "As a customer, I want a full portal so that I can manage everything.",
            "acceptance_criteria": [
                "Given the portal is available, when I log in, then I can access it.",
                "Given billing is available, when I open invoices, then billing data appears.",
                "Given notifications are available, when events happen, then alerts are sent.",
            ],
            "story_points": 13,
            "tasks": {"be": ["Build portal APIs"], "fe": ["Build portal UI"], "qa": ["Test portal"]},
            "definition_of_done": [
                "All acceptance criteria pass with validation evidence.",
                "BE and FE implementation tasks are complete.",
                "QA scenarios cover validation.",
                "Story is reviewed for Jira readiness.",
            ],
            "planning_status": "READY",
            "warnings": [],
        }
    )
    crew = build_crew({"documents": [], "retrieved_sources": [], "matches": [], "retrieval_status": "empty", "warnings": [], "confidence": 0.0}, planner)

    result = crew.run("Build a full portal with authentication, billing, admin dashboard, notifications, analytics, reporting, permissions, and audit logs.", allow_fallback_without_context=True)

    assert result["evaluation"]["status"] == "REVISION"
    assert result["story"]["planning_status"] == "SPLIT_RECOMMENDED"
    assert result["actions"]["jira"]["ready"] is False
    assert result["actions"]["slack"]["ready"] is False


def test_crew_post_generation_validation_sets_correct_ambiguous_status() -> None:
    planner = FakePlanner(
        {
            "title": "Improve Onboarding",
            "story_type": "software_feature",
            "user_story": "As a user, I want onboarding so that I can start.",
            "acceptance_criteria": [
                "Given onboarding starts, when the user continues, then onboarding completes.",
                "Given onboarding fails, when the user retries, then onboarding continues.",
                "Given onboarding is complete, when the user exits, then progress is saved.",
            ],
            "story_points": 3,
            "tasks": {"be": ["Implement onboarding API"], "fe": ["Build onboarding UI"], "qa": ["Test onboarding"]},
            "definition_of_done": [
                "All acceptance criteria pass with validation evidence.",
                "BE and FE implementation tasks are complete.",
                "QA scenarios cover validation.",
                "Story is reviewed for Jira readiness.",
            ],
            "planning_status": "READY",
            "clarification_questions": [],
            "warnings": [],
        }
    )
    crew = build_crew({"documents": [], "retrieved_sources": [], "matches": [], "retrieval_status": "empty", "warnings": [], "confidence": 0.0}, planner)

    result = crew.run("Improve onboarding", allow_fallback_without_context=True)

    assert result["evaluation"]["status"] == "REVISION"
    assert result["story"]["planning_status"] == "NEEDS_CLARIFICATION"
    assert result["actions"]["jira"]["ready"] is False
    assert result["actions"]["slack"]["ready"] is False
