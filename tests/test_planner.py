import inspect

from ai_scrum_master.agents.planner import PlannerAgent
from ai_scrum_master.core.domain_profiles import PLANNER_EVIDENCE_TEMPLATES, SPLIT_CAPABILITIES


def test_planner_evidence_templates_are_centralized() -> None:
    source = inspect.getsource(PlannerAgent)

    assert "auth" in PLANNER_EVIDENCE_TEMPLATES
    assert "Given a returning user starts Google OAuth sign-in" not in source
    assert "Implement retry-safe checkout payment handling" not in source
    assert "Which checkout step should be improved" not in source


def test_planner_split_capabilities_are_centralized() -> None:
    source = inspect.getsource(PlannerAgent._named_capabilities)

    assert "authentication" in SPLIT_CAPABILITIES
    assert '"billing"' not in source


class FakeLLM:
    def __init__(self, output: str) -> None:
        self.output = output
        self.messages = []
        self.prompt = ""

    def call(self, messages: list[dict[str, str]]) -> str:
        self.messages = messages
        self.prompt = "\n".join(message["content"] for message in messages)
        return self.output


class FakeLLMSequence:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = outputs
        self.messages = []
        self.calls = 0

    def call(self, messages: list[dict[str, str]]) -> str:
        self.messages = messages
        output = self.outputs[min(self.calls, len(self.outputs) - 1)]
        self.calls += 1
        return output


class BrokenLLM:
    def call(self, prompt: str) -> str:
        raise RuntimeError("ollama unavailable")


def test_planner_completes_missing_ready_fields_from_evidence() -> None:
    planner = PlannerAgent(
        llm=FakeLLM(
            """
            {
              "title": "Google Login",
              "user_story": "As a returning user, I want Google login so that I can sign in faster.",
              "acceptance_criteria": [
                "Given Google auth is enabled, when I click login, then OAuth starts."
              ],
              "story_points": 5,
              "tasks": {"be": ["Add OAuth callback"], "fe": [], "qa": []},
              "definition_of_done": [],
              "planning_status": "READY",
              "warnings": []
            }
            """
        )
    )

    result = planner.run(
        requirement="Add Google login",
        context={
            "documents": ["Auth stack uses JWT and Google OAuth."],
            "retrieved_sources": [{"source": "auth.md", "chunk_index": 0, "score": 0.9, "excerpt": "Auth uses Google OAuth."}],
            "warnings": [],
            "confidence": 0.9,
            "retrieval_status": "ok",
        },
    )

    assert result["title"] == "Google Login"
    assert len(result["acceptance_criteria"]) == 3
    assert result["acceptance_criteria"][0] == "Given Google auth is enabled, when I click login, then OAuth starts."
    assert result["tasks"]["be"] == ["Add OAuth callback"]
    assert result["tasks"]["fe"]
    assert result["tasks"]["qa"]
    assert len(result["definition_of_done"]) == 4
    assert result["latency_ms"] >= 0
    assert "planner_ms" in result["stage_latencies_ms"]
    assert "planner_initial_llm_ms" in result["stage_latencies_ms"]
    assert any("completed missing READY fields" in warning for warning in result["warnings"])


def test_planner_classifies_benchmark_route_as_ready_for_long_issue_text() -> None:
    planner = PlannerAgent(use_llm=False)
    requirement = " ".join(["Fix bounded astropy BlackBody scale validation bug"] * 8)

    result = planner.run(
        requirement=requirement,
        context={
            "documents": ["BlackBody scale validation issue."],
            "retrieved_sources": [{"source": "swe_bench_issues/example.md", "chunk_index": 0, "score": 0.9, "excerpt": "Scale validation bug."}],
            "warnings": [],
            "confidence": 0.9,
            "retrieval_status": "ok",
            "route": {"domain": "benchmark_case", "story_type": "software_feature"},
        },
        route={"domain": "benchmark_case", "story_type": "software_feature"},
    )

    assert result["planning_status"] == "REVISION"
    assert result["story_type"] == "software_feature"
    assert "Planner requires an LLM-generated" in result["warnings"][-1]


def test_planner_still_splits_large_non_benchmark_requests() -> None:
    planner = PlannerAgent(use_llm=False)

    result = planner.run(
        requirement="Build a full portal with authentication, billing, analytics, notifications, admin dashboard, permissions, and reporting.",
        context={"documents": [], "warnings": [], "confidence": 0.0},
    )

    assert result["planning_status"] == "SPLIT_RECOMMENDED"


def test_planner_returns_revision_shape_when_llm_is_unavailable() -> None:
    planner = PlannerAgent(llm=BrokenLLM())

    result = planner.run(
        requirement="Add Google login",
        context={
            "documents": ["Auth stack uses JWT and Google OAuth."],
            "retrieved_sources": [{"source": "auth.md", "chunk_index": 0, "score": 0.9, "excerpt": "Auth uses Google OAuth."}],
            "warnings": [],
            "confidence": 0.9,
            "retrieval_status": "ok",
        },
    )

    assert result["title"] == "Add Google login"
    assert result["user_story"] == ""
    assert result["acceptance_criteria"] == []
    assert result["tasks"] == {"be": [], "fe": [], "qa": []}
    assert result["definition_of_done"] == []
    assert result["fallback_used"] is False
    assert result["failure_type"] == "planner_exception"
    assert result["latency_ms"] >= 0
    assert "planner_ms" in result["stage_latencies_ms"]
    assert any("no fixed template fallback" in warning for warning in result["warnings"])
    assert any("planner_exception" in warning for warning in result["warnings"])


def test_planner_keeps_llm_planning_status_for_evaluator_review() -> None:
    planner = PlannerAgent(
        llm=FakeLLM(
            """
            {
              "title": "Google Login",
              "user_story": "As a returning user, I want Google login so that I can sign in faster.",
              "acceptance_criteria": [
                "Given Google auth is enabled, when I click login, then OAuth starts.",
                "Given OAuth succeeds, when callback returns, then I am signed in.",
                "Given OAuth fails, when callback returns, then I see an error."
              ],
              "story_points": 5,
              "tasks": {"be": ["Add OAuth callback"], "fe": ["Add button"], "qa": ["Test login"]},
              "definition_of_done": ["OAuth acceptance criteria are validated."],
              "planning_status": "READY",
              "warnings": []
            }
            """
        )
    )

    result = planner.run(
        requirement="Add Google login",
        context={"documents": ["Auth stack uses JWT and Google OAuth."], "warnings": [], "confidence": 0.8},
    )

    assert result["planning_status"] == "READY"


def test_planner_completes_weak_ready_output_from_evidence_without_extra_llm_calls() -> None:
    planner = PlannerAgent(
        llm=FakeLLMSequence(
            [
                """
                {
                  "title": "Google Login",
                  "user_story": "As a returning user, I want Google login so that I can sign in faster.",
                  "acceptance_criteria": ["Given Google auth is enabled, when I click login, then OAuth starts."],
                  "story_points": 3,
                  "tasks": {"be": ["Add OAuth callback"], "fe": [], "qa": []},
                  "definition_of_done": [],
                  "planning_status": "READY",
                  "warnings": []
                }
                """
            ]
        )
    )

    result = planner.run(
        requirement="Add Google login",
        context={
            "documents": ["Auth stack uses JWT and Google OAuth."],
            "retrieved_sources": [{"source": "auth.md", "chunk_index": 0, "score": 0.9, "excerpt": "Auth uses Google OAuth."}],
            "warnings": [],
            "confidence": 0.9,
            "retrieval_status": "ok",
        },
    )

    assert planner.llm.calls == 1
    assert result["repair_attempts_used"] == 0
    assert "planner_repair_llm_ms" not in result["stage_latencies_ms"]
    assert any("completed missing READY fields" in warning for warning in result["warnings"])


def test_planner_compacts_long_requirement_before_prompting() -> None:
    planner = PlannerAgent(
        llm=FakeLLM(
            """
            {
              "title": "Long benchmark issue",
              "user_story": "As a user, I want the documented issue fixed so that the expected behavior is restored.",
              "acceptance_criteria": [
                "Given documented behavior, when the issue is reproduced, then the expected behavior is restored."
              ],
              "story_points": 3,
              "tasks": {"be": ["Implement backend fix"], "fe": [], "qa": []},
              "definition_of_done": [],
              "planning_status": "READY",
              "warnings": []
            }
            """
        )
    )
    requirement = "Fix issue. " + ("long details " * 600)

    planner.run(
        requirement=requirement,
        context={"documents": ["Documented issue behavior."], "warnings": [], "confidence": 0.8},
    )

    current_requirement = planner.llm.prompt.split("CURRENT_REQUIREMENT:", 1)[1].split("PLANNING_STATUS_FROM_LOCAL_RULES:", 1)[0]
    assert "...[truncated]" in current_requirement
    assert len(current_requirement) < 3000


def test_planner_filters_unrelated_context_before_prompting() -> None:
    planner = PlannerAgent(
        llm=FakeLLM(
            """
            {
              "title": "Google Login",
              "user_story": "As a returning user, I want Google login so that I can sign in faster.",
              "acceptance_criteria": [
                "Given Google auth is enabled, when I click login, then OAuth starts."
              ],
              "story_points": 5,
              "tasks": {"be": ["Add OAuth callback"], "fe": [], "qa": []},
              "definition_of_done": [],
              "planning_status": "READY",
              "context_sources": [{"source": "auth_context.md", "chunk_index": 0, "score": 0.84, "excerpt": "Auth Context uses JWT authentication and OAuth callback endpoints."}],
              "warnings": []
            }
            """
        )
    )

    result = planner.run(
        requirement="As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password",
        context={
            "documents": ["Auth uses JWT and Google OAuth.", "Sprint Planning creates a Sprint Goal."],
            "context_snippets": [
                "[1] source=auth_context.md chunk=0 score=0.84: Auth Context uses JWT authentication and OAuth callback endpoints.",
                "[2] source=scrum_guide_2020.pdf chunk=16 score=0.77: Sprint Planning creates a Sprint Goal and Sprint Backlog.",
            ],
            "matches": [
                {"id": "auth-1", "document": "Auth Context uses JWT authentication and OAuth callback endpoints.", "metadata": {"source": "auth_context.md"}, "score": 0.84},
                {"id": "scrum-1", "document": "Sprint Planning creates a Sprint Goal and Sprint Backlog.", "metadata": {"source": "scrum_guide_2020.pdf"}, "score": 0.77},
            ],
            "retrieved_sources": [
                {"id": "auth-1", "source": "auth_context.md", "chunk_index": 0, "score": 0.84, "excerpt": "Auth Context uses JWT authentication and OAuth callback endpoints."},
                {"id": "scrum-1", "source": "scrum_guide_2020.pdf", "chunk_index": 16, "score": 0.77, "excerpt": "Sprint Planning creates a Sprint Goal and Sprint Backlog."},
            ],
            "warnings": [],
            "confidence": 0.8,
            "retrieval_status": "ok",
        },
    )

    current_context = planner.llm.prompt.split("SELECTED_RETRIEVED_CONTEXT:", 1)[1].split("RESEARCH_PLANNING_BRIEF:", 1)[0]
    assert "OAuth callback endpoints" in current_context
    assert "Sprint Goal" not in current_context
    assert result["context_sources"][0]["source"] == "auth_context.md"


def test_planner_sanitizes_unrelated_domain_from_llm_output_without_replacing_it() -> None:
    planner = PlannerAgent(
        llm=FakeLLM(
            """
            {
              "title": "Sprint Planning Google Login",
              "user_story": "As a Scrum Team member, I want Sprint Planning so that the Sprint Goal is clear.",
              "acceptance_criteria": [
                "Given the Sprint Goal is reviewed, when Product Backlog items are selected, then Sprint Planning is complete."
              ],
              "story_points": 3,
              "tasks": {"be": ["Define Product Backlog readiness criteria"], "fe": ["Create Sprint Goal template"], "qa": ["Run Scrum Team validation session"]},
              "definition_of_done": ["The Sprint Goal is agreed and Product Backlog items are selected."],
              "planning_status": "READY",
              "warnings": []
            }
            """
        )
    )

    result = planner.run(
        requirement="As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password.",
        context={"documents": ["Auth uses JWT and Google OAuth."], "warnings": [], "confidence": 0.9},
    )

    serialized = str(result).lower()
    assert "sprint goal" not in serialized
    assert result["user_story"] == ""
    assert result["acceptance_criteria"] == []
    assert any("unrelated-domain" in warning for warning in result["warnings"])


def test_planner_parses_wrapped_story_payload() -> None:
    planner = PlannerAgent(
        llm=FakeLLM(
            """
            {
              "confidence": 0.8,
              "story": {
                "title": "Google Login",
                "user_story": "As a returning user, I want Google login so that I can sign in faster.",
                "acceptance_criteria": [],
                "story_points": 5,
                "tasks": {"be": [], "fe": [], "qa": []},
                "definition_of_done": [],
                "planning_status": "READY",
                "warnings": []
              }
            }
            """
        )
    )

    result = planner.run(
        requirement="Add Google login",
        context={"documents": ["Auth stack uses JWT and Google OAuth."], "warnings": [], "confidence": 0.8},
    )

    assert result["title"] == "Google Login"


def test_planner_clarification_output_does_not_keep_ready_story_fields() -> None:
    planner = PlannerAgent(
        llm=FakeLLMSequence(
            [
                """
                {
                  "title": "Improve JWT login",
                  "story_type": "software_feature",
                  "user_story": "As a user, I want improved login so that sessions are better.",
                  "acceptance_criteria": [
                    "Given login exists, when the user signs in, then JWT works."
                  ],
                  "story_points": 3,
                  "tasks": {"be": ["Improve JWT backend"], "fe": ["Improve login page"], "qa": ["Test login"]},
                  "definition_of_done": ["Acceptance criteria pass with QA validation."],
                  "planning_status": "NEEDS_CLARIFICATION",
                  "clarification_questions": ["What exactly should be improved?"],
                  "warnings": []
                }
                """,
                """
                {
                  "title": "Clarify login improvement request",
                  "story_type": "ambiguous_request",
                  "user_story": "",
                  "acceptance_criteria": [],
                  "story_points": null,
                  "tasks": {"be": [], "fe": [], "qa": []},
                  "definition_of_done": [],
                  "planning_status": "NEEDS_CLARIFICATION",
                  "clarification_questions": [
                    "Which user or role is affected by the login improvement?",
                    "What login behavior or outcome should change?",
                    "Which constraints, success criteria, or failure cases should be covered before planning?"
                  ],
                  "warnings": []
                }
                """,
            ]
        )
    )

    result = planner.run(
        requirement="Improve login",
        context={
            "documents": ["Auth stack uses JWT and Google OAuth."],
            "retrieved_sources": [{"source": "auth.md", "chunk_index": 0, "score": 0.9, "excerpt": "Auth uses Google OAuth."}],
            "warnings": [],
            "confidence": 0.9,
            "retrieval_status": "ok",
        },
    )

    assert result["planning_status"] == "NEEDS_CLARIFICATION"
    assert result["story_type"] == "ambiguous_request"
    assert result["user_story"] == ""
    assert result["acceptance_criteria"] == []
    assert result["story_points"] is None
    assert result["tasks"] == {"be": [], "fe": [], "qa": []}
    assert result["definition_of_done"] == []
    assert len(result["clarification_questions"]) == 3
