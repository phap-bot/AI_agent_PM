from ai_scrum_master.agents.evaluator import EvaluatorAgent


class FakeLLM:
    def __init__(self, output: str) -> None:
        self.output = output

    def call(self, prompt: str) -> str:
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


def test_evaluator_revises_oversized_story_without_split_details() -> None:
    evaluator = EvaluatorAgent(use_llm=False)
    story = {**VALID_STORY, "planning_status": "SPLIT_RECOMMENDED"}

    result = evaluator.run(story)

    assert result["status"] == "REVISION"
    assert any("story_splits" in issue for issue in result["issues"])
    assert any("sprint_allocation" in issue for issue in result["issues"])
