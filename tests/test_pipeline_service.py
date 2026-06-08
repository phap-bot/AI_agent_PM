from ai_scrum_master.core.pipeline import generate_story_pipeline


class FakeCrewAiCrew:
    def __init__(self) -> None:
        self.kickoff_inputs = None

    def kickoff(self, inputs: dict) -> dict:
        self.kickoff_inputs = inputs
        return {"status": "ok"}


class FakeDeterministicCrew:
    def run(self, requirement: str, n_results: int = 5, allow_fallback_without_context: bool = False, progress_callback=None) -> dict:
        return {
            "context": {"retrieval_status": "ok", "warnings": []},
            "story": {"title": requirement, "planning_status": "READY"},
            "evaluation": {"status": "APPROVED", "issues": [], "revision_instructions": [], "warnings": []},
            "actions": {"jira": {"ready": False}, "slack": {"ready": False}},
        }


class FailingDeterministicCrew:
    def run(self, *args, **kwargs) -> dict:
        raise AssertionError("deterministic crew should not run when CrewAI returns a complete response")


def test_generate_story_pipeline_invokes_crewai_crew_when_builder_is_supplied() -> None:
    crewai_crew = FakeCrewAiCrew()

    result = generate_story_pipeline(
        requirement="Add Google login",
        n_results=3,
        allow_fallback_without_context=True,
        crew=FakeDeterministicCrew(),
        crewai_builder=lambda requirement, n_results: crewai_crew,
    )

    assert crewai_crew.kickoff_inputs == {
        "requirement": "Add Google login",
        "n_results": 3,
        "allow_fallback_without_context": True,
    }
    assert result["story"]["title"] == "Add Google login"


def test_generate_story_pipeline_uses_complete_crewai_response() -> None:
    class CompleteCrewAiCrew(FakeCrewAiCrew):
        def kickoff(self, inputs: dict) -> dict:
            super().kickoff(inputs)
            return {
                "context": {"retrieval_status": "ok", "warnings": []},
                "story": {
                    "title": "CrewAI Google Login",
                    "user_story": "As a user, I want Google login so that I can sign in faster.",
                    "acceptance_criteria": [],
                    "tasks": {"be": [], "fe": [], "qa": []},
                    "definition_of_done": [],
                    "planning_status": "READY",
                },
                "evaluation": {"status": "APPROVED", "issues": [], "revision_instructions": [], "warnings": []},
                "actions": {
                    "jira": {"ready": False, "payload": None, "warnings": []},
                    "slack": {"ready": False, "payload": None, "warnings": []},
                },
            }

    crewai_crew = CompleteCrewAiCrew()

    result = generate_story_pipeline(
        requirement="Add Google login",
        n_results=3,
        crew=FailingDeterministicCrew(),
        crewai_builder=lambda requirement, n_results: crewai_crew,
    )

    assert result["story"]["title"] == "CrewAI Google Login"


def test_generate_story_pipeline_revises_invalid_crewai_response() -> None:
    class InvalidCrewAiCrew(FakeCrewAiCrew):
        def kickoff(self, inputs: dict) -> dict:
            super().kickoff(inputs)
            return {
                "context": {"retrieval_status": "ok", "warnings": []},
                "story": "this is not a dictionary",
                "evaluation": {"status": "APPROVED", "issues": [], "revision_instructions": [], "warnings": []},
                "actions": {
                    "jira": {"ready": True, "payload": {"summary": "bad"}, "warnings": []},
                    "slack": {"ready": True, "payload": {"text": "bad"}, "warnings": []},
                },
            }

    result = generate_story_pipeline(
        requirement="Add Google login",
        crew=FailingDeterministicCrew(),
        crewai_builder=lambda requirement, n_results: InvalidCrewAiCrew(),
    )

    assert result["evaluation"]["status"] == "REVISION"
    assert result["actions"]["jira"]["ready"] is False
    assert result["actions"]["slack"]["ready"] is False
    assert any("CrewAI structured output failed validation" in warning for warning in result["evaluation"]["warnings"])


def test_generate_story_pipeline_revises_schema_valid_but_low_quality_crewai_story() -> None:
    class WeakCrewAiCrew(FakeCrewAiCrew):
        def kickoff(self, inputs: dict) -> dict:
            super().kickoff(inputs)
            return {
                "context": {
                    "retrieval_status": "ok",
                    "retrieved_sources": [
                        {"source": "auth_context.md", "excerpt": "Google OAuth callback JWT session.", "score": 0.9}
                    ],
                    "selected_context_sources": [
                        {"source": "auth_context.md", "excerpt": "Google OAuth callback JWT session.", "score": 0.9}
                    ],
                    "warnings": [],
                },
                "story": {
                    "title": "Weak Google Login",
                    "story_type": "software_feature",
                    "user_story": "As a user, I want login so that I can access the app.",
                    "acceptance_criteria": ["Given login starts, when it works, then access is granted."],
                    "story_points": 3,
                    "tasks": {"be": ["Define backend changes"], "fe": ["Define UI or client impact"], "qa": ["Prepare validation scenarios"]},
                    "definition_of_done": ["Done."],
                    "planning_status": "READY",
                },
                "evaluation": {"status": "APPROVED", "issues": [], "revision_instructions": [], "warnings": []},
                "actions": {
                    "jira": {"ready": True, "payload": {"summary": "bad"}, "warnings": []},
                    "slack": {"ready": True, "payload": {"text": "bad"}, "warnings": []},
                },
            }

    result = generate_story_pipeline(
        requirement="As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password.",
        crew=FailingDeterministicCrew(),
        crewai_builder=lambda requirement, n_results: WeakCrewAiCrew(),
    )

    assert result["story"]["planning_status"] == "REVISION"
    assert result["evaluation"]["status"] == "REVISION"
    assert result["actions"]["jira"]["ready"] is False
    assert any("READY stories require at least 3 acceptance criteria" in issue for issue in result["evaluation"]["issues"])


def test_generate_story_pipeline_ignores_crewai_action_readiness() -> None:
    class ActionLeakingCrewAiCrew(FakeCrewAiCrew):
        def kickoff(self, inputs: dict) -> dict:
            super().kickoff(inputs)
            story = {
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
                    "be": ["Implement Google OAuth callback endpoint and exchange provider code server-side."],
                    "fe": ["Add Sign in with Google button and handle cancelled authentication error display."],
                    "qa": ["Test successful Google sign-in, cancelled authentication, email mapping, and token URL exposure."],
                },
                "definition_of_done": [
                    "All Google OAuth acceptance criteria pass.",
                    "Backend exchanges provider code and creates JWT API session.",
                    "Frontend handles success and cancelled or rejected authentication.",
                    "QA verifies email mapping and tokens are not exposed in URL query parameters.",
                ],
                "planning_status": "READY",
            }
            return {
                "context": {
                    "retrieval_status": "ok",
                    "retrieved_sources": [
                        {"source": "auth_context.md", "excerpt": "Google OAuth callback JWT session.", "score": 0.9}
                    ],
                    "selected_context_sources": [
                        {"source": "auth_context.md", "excerpt": "Google OAuth callback JWT session.", "score": 0.9}
                    ],
                    "warnings": [],
                },
                "story": story,
                "evaluation": {"status": "APPROVED", "issues": [], "revision_instructions": [], "warnings": []},
                "actions": {
                    "jira": {"ready": True, "payload": {"summary": "agent-owned"}, "warnings": []},
                    "slack": {"ready": True, "payload": {"text": "agent-owned"}, "warnings": []},
                },
            }

    result = generate_story_pipeline(
        requirement="As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password.",
        crew=FailingDeterministicCrew(),
        crewai_builder=lambda requirement, n_results: ActionLeakingCrewAiCrew(),
    )

    assert result["evaluation"]["status"] == "APPROVED"
    assert result["actions"]["jira"]["payload"] != {"summary": "agent-owned"}
    assert result["actions"]["slack"]["payload"] != {"text": "agent-owned"}
