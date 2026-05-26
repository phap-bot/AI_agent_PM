from ai_scrum_master.agents.planner import PlannerAgent


class FakeLLM:
    def __init__(self, output: str) -> None:
        self.output = output
        self.prompt = ""

    def call(self, prompt: str) -> str:
        self.prompt = prompt
        return self.output


class BrokenLLM:
    def call(self, prompt: str) -> str:
        raise RuntimeError("ollama unavailable")


def test_planner_generates_story_shape_without_llm() -> None:
    planner = PlannerAgent(use_llm=False)
    result = planner.run(
        requirement="Add Google login",
        context={"documents": ["auth stack uses JWT"], "warnings": [], "confidence": 0.8},
    )

    assert result["title"]
    assert result["user_story"].startswith("As a")
    assert len(result["acceptance_criteria"]) >= 3
    assert set(result["tasks"].keys()) == {"be", "fe", "qa"}
    assert result["story_points"] in {1, 2, 3, 5, 8, 13}
    assert len(result["definition_of_done"]) >= 4
    assert len(result["tasks"]["be"]) >= 2
    assert len(result["tasks"]["fe"]) >= 2
    assert len(result["tasks"]["qa"]) >= 2


def test_planner_parses_llm_json_output() -> None:
    planner = PlannerAgent(
        llm=FakeLLM(
            """
            {
              "title": "Google Login",
              "user_story": "As a user, I want Google login so that I can sign in faster.",
              "acceptance_criteria": [
                "Given Google auth is enabled, when I click login, then OAuth starts.",
                "Given OAuth succeeds, when callback returns, then I am signed in.",
                "Given OAuth fails, when callback returns, then I see an error."
              ],
              "story_points": 5,
              "tasks": {"be": ["Add OAuth callback"], "fe": ["Add button"], "qa": ["Test login"]},
              "definition_of_done": ["AC pass"],
              "warnings": []
            }
            """
        )
    )

    result = planner.run(
        requirement="Add Google login",
        context={"documents": ["auth stack uses JWT"], "warnings": [], "confidence": 0.8},
    )

    assert "definition_of_done must include detailed completion checks" in planner.llm.prompt
    assert result["title"] == "Google Login"
    assert result["story_points"] == 5
    assert result["tasks"]["be"] == ["Add OAuth callback"]


def test_planner_falls_back_when_llm_fails() -> None:
    planner = PlannerAgent(llm=BrokenLLM())
    result = planner.run(
        requirement="Add Google login",
        context={"documents": [], "warnings": [], "confidence": 0.0},
    )

    assert result["title"] == "Draft Scrum Story"
    assert any("Planner LLM unavailable" in warning for warning in result["warnings"])


def test_planner_marks_ambiguous_requirement_for_clarification_without_llm() -> None:
    planner = PlannerAgent(use_llm=False)
    result = planner.run(
        requirement="Improve login",
        context={"documents": [], "warnings": [], "confidence": 0.0},
    )

    assert result["planning_status"] == "NEEDS_CLARIFICATION"
    assert len(result["clarification_questions"]) >= 3
    assert any("clarification" in warning.lower() for warning in result["warnings"])


def test_planner_recommends_split_for_oversized_requirement_without_llm() -> None:
    planner = PlannerAgent(use_llm=False)
    result = planner.run(
        requirement="Build a full customer portal with auth, billing, admin dashboard, notifications, and analytics",
        context={"documents": [], "warnings": [], "confidence": 0.0},
    )

    assert result["planning_status"] == "SPLIT_RECOMMENDED"
    assert len(result["story_splits"]) >= 2
    assert result["sprint_allocation"]


def test_planner_preserves_oversized_classifier_when_llm_returns_ready() -> None:
    planner = PlannerAgent(
        llm=FakeLLM(
            """
            {
              "title": "Full Customer Portal",
              "user_story": "As a Customer, I want to authenticate myself so that I can access the portal features.",
              "acceptance_criteria": [
                "Given login is available, when I authenticate, then I can access the portal.",
                "Given billing is available, when I open billing, then I can view invoices.",
                "Given admin profile management is available, when an admin edits a profile, then changes are saved."
              ],
              "story_points": 13,
              "tasks": {"be": ["Build portal APIs"], "fe": ["Build portal UI"], "qa": ["Prepare validation scenarios"]},
              "definition_of_done": ["Acceptance criteria pass."],
              "planning_status": "READY",
              "warnings": []
            }
            """
        )
    )

    result = planner.run(
        requirement="Build a full customer portal with authentication, billing, admin dashboard, notifications, analytics, profile management, and reporting.",
        context={"documents": ["Large stakeholder requests should become multiple stories across multiple sprints."], "warnings": [], "confidence": 0.9},
    )

    assert result["planning_status"] == "SPLIT_RECOMMENDED"
    assert result["story_splits"]
    assert result["sprint_allocation"]
    assert any("conflicts with local classifier" in warning for warning in result["warnings"])


def test_planner_normalizes_split_story_noise() -> None:
    planner = PlannerAgent(
        llm=FakeLLM(
            """
            {
              "title": "Full Customer Portal",
              "user_story": "As a customer, I want a portal so that I can manage my account.",
              "acceptance_criteria": [],
              "story_points": 13,
              "tasks": {},
              "definition_of_done": [],
              "planning_status": "SPLIT_RECOMMENDED",
              "story_splits": [{
                "title": "Customer Portal Authentication",
                "user_story": "As a customer, I want to authenticate so that I can access my account.",
                "acceptance_criteria": ["Given login starts, when credentials pass, then access is granted."],
                "story_points": 5,
                "tasks": {"be": [], "fe": [], "qa": []},
                "definition_of_done": [],
                "planning_status": "READY",
                "clarification_questions": ["Noise"],
                "sprint_allocation": ["Sprint 1"]
              }],
              "sprint_allocation": [{"sprint": 1, "stories": ["Customer Portal Authentication"]}],
              "warnings": []
            }
            """
        )
    )

    result = planner.run(
        requirement="Build a full customer portal with authentication, billing, admin dashboard, notifications, analytics, profile management, and reporting.",
        context={"documents": [], "warnings": [], "confidence": 0.0},
    )

    split = result["story_splits"][0]
    assert set(split.keys()) == {"title", "user_story", "acceptance_criteria", "story_points", "tasks", "definition_of_done"}
    assert len(split["acceptance_criteria"]) >= 3
    assert split["tasks"]["be"]
    assert split["tasks"]["fe"]
    assert split["tasks"]["qa"]
    assert split["definition_of_done"]


def test_planner_falls_back_when_llm_returns_invalid_json() -> None:
    planner = PlannerAgent(llm=FakeLLM("not json"))
    result = planner.run(
        requirement="Add Google login",
        context={"documents": [], "warnings": [], "confidence": 0.0},
    )

    assert result["title"] == "Draft Scrum Story"
    assert any("Planner LLM unavailable" in warning for warning in result["warnings"])


def test_planner_normalizes_incomplete_llm_output() -> None:
    planner = PlannerAgent(
        llm=FakeLLM(
            """
            {
              "title": "Google Login",
              "user_story": "As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password.",
              "acceptance_criteria": [
                "Given Google sign-in is enabled, when I choose Google login, then the OAuth flow starts."
              ],
              "story_points": 5,
              "tasks": {"be": [], "fe": [], "qa": []},
              "definition_of_done": [],
              "planning_status": "READY",
              "clarification_questions": ["Is the user already logged in on their device?"],
              "sprint_allocation": [{"sprint": 1, "start_date": "2023-10-05", "stories": ["Google Login"]}],
              "warnings": []
            }
            """
        )
    )

    result = planner.run(
        requirement="As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password.",
        context={"documents": ["Auth uses FastAPI and JWT sessions."], "warnings": [], "confidence": 0.8},
    )

    assert result["planning_status"] == "READY"
    assert result["clarification_questions"] == []
    assert result["sprint_allocation"] == []
    assert len(result["acceptance_criteria"]) >= 3
    assert all("given" in criterion.lower() and "when" in criterion.lower() and "then" in criterion.lower() for criterion in result["acceptance_criteria"])
    assert result["tasks"]["be"]
    assert result["tasks"]["fe"]
    assert result["tasks"]["qa"]
    assert len(result["definition_of_done"]) >= 4
    assert any("acceptance criteria" in item.lower() for item in result["definition_of_done"])
    assert any("qa" in item.lower() or "test" in item.lower() for item in result["definition_of_done"])


def test_planner_rejects_given_when_then_substrings() -> None:
    planner = PlannerAgent(
        llm=FakeLLM(
            """
            {
              "title": "Google Login",
              "user_story": "As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password.",
              "acceptance_criteria": [
                "Given the user cancels authentication, when the frontend displays an error message."
              ],
              "story_points": 5,
              "tasks": {"be": ["Add callback"], "fe": ["Show error"], "qa": ["Test error"]},
              "definition_of_done": ["Acceptance criteria pass."],
              "planning_status": "READY",
              "warnings": []
            }
            """
        )
    )

    result = planner.run(
        requirement="As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password.",
        context={"documents": ["Auth uses FastAPI and JWT sessions."], "warnings": [], "confidence": 0.8},
    )

    assert all(" then " in f" {criterion.lower()} " for criterion in result["acceptance_criteria"])


def test_planner_completes_shallow_definition_of_done() -> None:
    planner = PlannerAgent(
        llm=FakeLLM(
            """
            {
              "title": "Google Login",
              "user_story": "As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password.",
              "acceptance_criteria": [
                "Given Google sign-in is enabled, when I choose Google login, then the OAuth flow starts.",
                "Given OAuth succeeds, when callback returns, then I am signed in.",
                "Given OAuth fails, when callback returns, then I see an error."
              ],
              "story_points": 5,
              "tasks": {"be": ["Add OAuth callback"], "fe": ["Add Google login button"], "qa": ["Test Google login flow"]},
              "definition_of_done": ["AC pass"],
              "planning_status": "READY",
              "warnings": []
            }
            """
        )
    )

    result = planner.run(
        requirement="As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password.",
        context={"documents": ["Auth uses FastAPI and JWT sessions."], "warnings": [], "confidence": 0.8},
    )

    assert "AC pass" in result["definition_of_done"]
    assert len(result["definition_of_done"]) >= 5
    assert any("Jira" in item for item in result["definition_of_done"])


def test_planner_keeps_sprint_allocation_only_for_split_recommended() -> None:
    planner = PlannerAgent(
        llm=FakeLLM(
            """
            {
              "title": "Customer Portal",
              "user_story": "As a customer, I want a full portal so that I can manage my account.",
              "acceptance_criteria": [],
              "story_points": 13,
              "tasks": {},
              "definition_of_done": [],
              "planning_status": "SPLIT_RECOMMENDED",
              "story_splits": [],
              "sprint_allocation": [{"sprint": 1, "start_date": "2023-10-05", "stories": ["Foundation"]}],
              "warnings": []
            }
            """
        )
    )

    result = planner.run(
        requirement="Build a full customer portal with auth, billing, admin dashboard, notifications, and analytics",
        context={"documents": [], "warnings": [], "confidence": 0.0},
    )

    assert result["planning_status"] == "SPLIT_RECOMMENDED"
    assert result["story_splits"]
    assert result["sprint_allocation"] == [{"sprint": 1, "stories": ["Foundation"]}]
    assert "start_date" not in result["sprint_allocation"][0]
