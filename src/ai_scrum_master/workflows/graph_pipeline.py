"""LangGraph-based pipeline for the AI Scrum Master multi-agent workflow.

Graph topology:
    route_requirement → researcher → [check_context]
        ├─ needs_context (stop)
        └─ planner → [check_planner_quality]
              ├─ researcher (retry)
              └─ evaluator → [check_evaluation]
                    ├─ finalize_approved → prepare_actions (stop)
                    ├─ researcher (retry)
                    └─ finalize_revision (stop)

Each node is a plain function: (PipelineState) -> partial PipelineState.
No helper classes, no wrapper abstractions — just functions.
"""
from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from ai_scrum_master.actions.jira import JiraTool
from ai_scrum_master.actions.slack import SlackTool
from ai_scrum_master.agents.evaluator import EvaluatorAgent
from ai_scrum_master.agents.planner import PlannerAgent
from ai_scrum_master.agents.researcher import ResearcherAgent
from ai_scrum_master.agents.router import RouterAgent
from ai_scrum_master.core.config.settings import get_runtime_profiles
from ai_scrum_master.core.pipeline.context_selector import select_context_for_route
from ai_scrum_master.core.pipeline.finalizer import blocked_actions, finalize_generation, should_block_planning
from ai_scrum_master.workflows.graph_state import PipelineState
from ai_scrum_master.core.utils.logging import get_logger
from ai_scrum_master.core.validation.quality import AMBIGUOUS_REQUEST, OVERSIZED_REQUEST, validate_story_against_requirement
from ai_scrum_master.core.pipeline.requirement_router import build_route_from_classification
from ai_scrum_master.core.validation.story_validator import evaluate_planner_output, validate_post_generation

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
#  NODES — each receives full state, returns only changed keys
# ═══════════════════════════════════════════════════════════════

def analyzer_node(state: PipelineState) -> dict[str, Any]:
    """Run RouterAgent to classify requirement and determine routing profile."""
    router = RouterAgent()
    logger.info("Graph node [analyzer] starting")
    classification = router.run(state["requirement"])
    
    # Build full route object from LLM classification
    route = build_route_from_classification(classification["domain"], classification["story_type"])
    requirement_type = classification["story_type"]
    
    logger.info("Graph node [analyzer] domain=%s type=%s", route.get("domain"), requirement_type)
    if classification.get("clarity_reasoning"):
        logger.info("Analyzer Clarity Reasoning: %s", classification["clarity_reasoning"])
    if classification.get("scope_reasoning"):
        logger.info("Analyzer Scope Reasoning: %s", classification["scope_reasoning"])
    
    return {
        "route": route, 
        "requirement_type": requirement_type,
        "tech_classification": {
            "domain": classification["domain"],
            "tech_stack": classification["tech_stack"],
            "search_keywords": classification["search_keywords"]
        }
    }


def researcher_node(state: PipelineState) -> dict[str, Any]:
    """Run the Researcher agent to retrieve context from vector store."""
    profiles = get_runtime_profiles()
    researcher = ResearcherAgent(
        profile=profiles.agents.get("researcher"),
        task_profile=profiles.tasks.get("research_task"),
    )

    iteration = state.get("iteration", 0) + 1
    logger.info("Graph node [researcher] iteration=%s feedback=%s", iteration, bool(state.get("research_feedback")))

    context = researcher.run(
        requirement=state["requirement"],
        n_results=state.get("n_results", 5),
        route=state.get("route", {}),
        forced_context_docs=state.get("forced_context_docs"),
        project_id=state.get("project_id"),
        feedback=state.get("research_feedback"),
    )
    context["route"] = state.get("route", {})

    cb = state.get("progress_callback")
    if cb:
        cb("researcher", {"raw_context": context})

    return {"raw_context": context, "iteration": iteration}


def merge_context_node(state: PipelineState) -> dict[str, Any]:
    """Merge parallel results: Apply context selection using the resolved route."""
    logger.info("Graph node [merge_context]")
    
    # Apply context selection for the requirement domain
    selected = select_context_for_route(state["requirement"], state["raw_context"], state["route"])
    selected["ignored_context_sources"] = [
        {
            "id": s.get("id", ""),
            "source": s.get("source", "unknown source"),
            "chunk_index": s.get("chunk_index", "?"),
            "score": s.get("score", 0.0),
            "ignored_reason": "unrelated_to_requirement_domain",
        }
        for s in selected.get("ignored_context_sources", [])
    ]

    cb = state.get("progress_callback")
    if cb:
        cb("merge_context", {"context": selected})

    return {"context": selected}


def planner_node(state: PipelineState) -> dict[str, Any]:
    """Run the Planner agent to generate User Story / AC / Tasks."""
    profiles = get_runtime_profiles()
    planner = PlannerAgent(
        profile=profiles.agents.get("planner"),
        task_profile=profiles.tasks.get("planning_task"),
    )

    logger.info("Graph node [planner] requirement_type=%s", state.get("requirement_type"))

    story = planner.run(
        requirement=state["requirement"],
        context=dict(state["context"]),
        requirement_type=state.get("requirement_type"),
        route=state["route"],
        tech_classification=state.get("tech_classification"),
    )
    story["requirement"] = state["requirement"]
    story["story_type"] = state.get("requirement_type", "software_feature")
    story["route"] = state["route"]

    # Run deterministic planner quality gate
    planner_quality = evaluate_planner_output(state.get("requirement_type", "software_feature"), state["requirement"], story, state["context"])
    story["planner_quality"] = planner_quality

    cb = state.get("progress_callback")
    if cb:
        cb("planner", {"story": story})

    return {"story": story, "planner_quality": planner_quality}


def evaluator_node(state: PipelineState) -> dict[str, Any]:
    """Run the Evaluator agent to score and approve/reject the story."""
    profiles = get_runtime_profiles()
    evaluator = EvaluatorAgent(
        profile=profiles.agents.get("evaluator"),
        task_profile=profiles.tasks.get("evaluation_task"),
    )

    logger.info("Graph node [evaluator] iteration=%s", state.get("iteration"))

    story = state["story"]
    evaluation = evaluator.run(story=story)

    # Apply runtime safety checks
    issues: list[str] = []
    if story.get("fallback_used"):
        issues.append("Planner fallback was used; human revision is required before downstream actions.")
    if state["context"].get("confidence", 1.0) < 0.5:
        issues.append("Retrieved context confidence is low; human revision is required before downstream actions.")
    if issues:
        evaluation = {
            "status": "REVISION",
            "issues": list(dict.fromkeys(evaluation.get("issues", []) + issues)),
            "revision_instructions": list(dict.fromkeys(evaluation.get("revision_instructions", []) + issues)),
            "dod_score": evaluation.get("dod_score", {}),
            "warnings": evaluation.get("warnings", []),
        }

    # Apply post-generation validation
    req_type = state.get("requirement_type", "software_feature")
    validation_issues = validate_story_against_requirement(req_type, state["requirement"], story)
    if validation_issues:
        logger.info("Post-generation validation failed issues=%s", len(validation_issues))
        if req_type == OVERSIZED_REQUEST:
            story["planning_status"] = "SPLIT_RECOMMENDED"
        elif req_type == AMBIGUOUS_REQUEST:
            story["planning_status"] = "NEEDS_CLARIFICATION"
        else:
            story["planning_status"] = "REVISION"
        all_issues = list(dict.fromkeys(evaluation.get("issues", []) + validation_issues))
        evaluation = {
            "status": "REVISION",
            "issues": all_issues,
            "revision_instructions": list(dict.fromkeys(evaluation.get("revision_instructions", []) + validation_issues)),
            "dod_score": evaluation.get("dod_score", {}),
            "warnings": evaluation.get("warnings", []),
        }

    # Apply finalize_generation deterministic checks
    evaluation = finalize_generation(story, evaluation)["evaluation"]

    issues = evaluation.get("issues", [])
    instructions = evaluation.get("revision_instructions", [])
    research_feedback = " ".join(issues + instructions) if (issues or instructions) else None

    cb = state.get("progress_callback")
    if cb:
        cb("evaluator", {"evaluation": evaluation})

    return {"story": story, "evaluation": evaluation, "research_feedback": research_feedback}


def needs_context_node(state: PipelineState) -> dict[str, Any]:
    """Terminal node: context retrieval failed or insufficient."""
    context = state["context"]
    route = state["route"]

    if context.get("missing_required_sources"):
        warning = f"Planner blocked because required context source(s) are missing: {', '.join(context['missing_required_sources'])}."
    else:
        warning = "Planner blocked because no relevant retrieved context met the configured threshold."

    logger.info("Graph node [needs_context] warning=%s", warning)
    return {
        "story": None,
        "evaluation": {
            "status": "NEEDS_CONTEXT",
            "issues": [warning],
            "revision_instructions": [
                "Import or ingest more relevant documentation, then rerun the requirement.",
                "Or rerun with allow_fallback_without_context=true to generate a clearly marked fallback story.",
            ],
            "warnings": context.get("warnings", []) + [warning],
        },
        "actions": {
            "jira": {"ready": False, "payload": None, "warnings": [warning]},
            "slack": {"ready": False, "payload": None, "warnings": [warning]},
        },
        "next_steps": [
            "Import or ingest documentation that describes this requirement.",
            "Rerun the same requirement after ingestion.",
            "If you intentionally want generic fallback output, set allow_fallback_without_context=true.",
        ],
    }


def finalize_approved_node(state: PipelineState) -> dict[str, Any]:
    """Terminal node: story APPROVED — prepare Jira/Slack actions."""
    story = state["story"]
    evaluation = state["evaluation"]
    project_id = state.get("project_id")

    jira_tool = JiraTool.from_project(project_id)
    slack_tool = SlackTool.from_project(project_id)

    logger.info("Graph node [finalize_approved] preparing actions")
    return {
        "actions": {
            "jira": jira_tool.prepare_action(story),
            "slack": slack_tool.prepare_action(story, evaluation),
        },
        "next_steps": [],
    }


def finalize_revision_node(state: PipelineState) -> dict[str, Any]:
    """Terminal node: story needs REVISION — block actions."""
    evaluation = state.get("evaluation")
    if not evaluation:
        pq = state.get("planner_quality", {})
        warning = "Planner quality gate failed; evaluator was not run because the story is not ready for evaluation."
        failures = list(dict.fromkeys(pq.get("failures", []) + [warning]))
        evaluation = {
            "status": "REVISION",
            "issues": failures,
            "revision_instructions": failures,
            "dod_score": {},
            "warnings": [warning],
        }

    logger.info("Graph node [finalize_revision] status=%s", evaluation.get("status"))
    return {
        "evaluation": evaluation,
        "actions": blocked_actions(),
        "next_steps": ["Review evaluator feedback and resubmit the requirement."],
    }


def finalize_clarification_node(state: PipelineState) -> dict[str, Any]:
    """Terminal node: requirement is ambiguous — return clarification questions immediately.

    This node short-circuits the pipeline: when the planner determines that a
    requirement needs clarification (NEEDS_CLARIFICATION), we return directly
    to the UI with the clarification questions instead of running the evaluator
    or retrying the researcher/planner loop (which would be pointless since the
    requirement itself is too vague to generate tasks).
    """
    story = state.get("story") or {}
    logger.info("Graph node [finalize_clarification] returning to UI for clarification")
    return {
        "evaluation": {
            "status": "NEEDS_CLARIFICATION",
            "issues": [],
            "revision_instructions": [],
            "dod_score": {},
            "warnings": ["Requirement cần được làm rõ trước khi lên kế hoạch Sprint."],
        },
        "actions": blocked_actions(),
        "next_steps": story.get("clarification_questions", []),
    }



# ═══════════════════════════════════════════════════════════════
#  CONDITIONAL EDGES — router functions that pick the next node
# ═══════════════════════════════════════════════════════════════

def after_researcher(state: PipelineState) -> Literal["planner", "needs_context"]:
    """After researcher: check if context is sufficient to proceed."""
    if should_block_planning(state["context"], state.get("allow_fallback_without_context", False)):
        return "needs_context"
    return "planner"


def after_planner(state: PipelineState) -> Literal["evaluator", "researcher", "finalize_revision", "finalize_clarification"]:
    """After planner: check planning_status and deterministic quality gate.

    Short-circuit rules:
    - NEEDS_CLARIFICATION → finalize_clarification (skip evaluator entirely)
    - SPLIT_RECOMMENDED/NEEDS_SPLIT → finalize_revision (no retry needed)
    - READY + quality gate passed → evaluator
    - READY + quality gate failed → retry researcher or finalize_revision
    """
    story = state.get("story") or {}
    planning_status = story.get("planning_status", "READY")

    # NEEDS_CLARIFICATION → return immediately, no evaluator, no retry
    if planning_status == "NEEDS_CLARIFICATION":
        logger.info("Graph router [after_planner] NEEDS_CLARIFICATION, short-circuiting to finalize_clarification")
        return "finalize_clarification"

    # SPLIT_RECOMMENDED/NEEDS_SPLIT → return immediately for human review
    if planning_status in {"SPLIT_RECOMMENDED", "NEEDS_SPLIT"}:
        logger.info("Graph router [after_planner] %s, short-circuiting to finalize_revision", planning_status)
        return "finalize_revision"

    # Quality gate check (only for READY stories)
    pq = state.get("planner_quality", {})
    if pq.get("passed", True):
        return "evaluator"

    # Quality gate failed — retry or give up
    if state.get("iteration", 1) <= state.get("max_retries", 2):
        logger.info("Graph router [after_planner] quality gate failed, retrying researcher")
        return "researcher"

    logger.info("Graph router [after_planner] quality gate failed, no retries left")
    return "finalize_revision"


def after_evaluator(state: PipelineState) -> Literal["finalize_approved", "researcher", "finalize_revision", "finalize_clarification"]:
    """After evaluator: route based on evaluation status.

    Smart retry: only retry when evaluator found fixable quality issues
    (missing AC, bad tasks, weak DoD). Do NOT retry for unfixable issues
    like NEEDS_CLARIFICATION or domain contamination.
    """
    evaluation = state.get("evaluation") or {}
    status = evaluation.get("status", "REVISION")
    story = state.get("story") or {}

    if status == "APPROVED":
        return "finalize_approved"

    # Post-validation may set NEEDS_CLARIFICATION → return immediately
    if story.get("planning_status") == "NEEDS_CLARIFICATION":
        logger.info("Graph router [after_evaluator] NEEDS_CLARIFICATION, short-circuiting")
        return "finalize_clarification"

    # Only retry when evaluator found fixable quality issues
    if _has_fixable_quality_issues(evaluation) and state.get("iteration", 1) <= state.get("max_retries", 2):
        logger.info("Graph router [after_evaluator] REVISION with fixable quality issues, retrying. feedback=%s", str(state.get("research_feedback", ""))[:100])
        return "researcher"

    # No fixable issues or retries exhausted → return to human
    logger.info("Graph router [after_evaluator] REVISION, no fixable issues or no retries left")
    return "finalize_revision"


def _has_fixable_quality_issues(evaluation: dict[str, Any]) -> bool:
    """Check if evaluation contains quality issues that can be improved by retrying.

    Retry when evaluator found concrete output quality problems:
    - Missing or insufficient Acceptance Criteria (< 3, no Given/When/Then)
    - Tasks not actionable (placeholder, user story format, missing group)
    - Weak Definition of Done (< 4 checks, low score)
    - Invalid story points (non-Fibonacci)

    Do NOT retry for:
    - NEEDS_CLARIFICATION (ambiguous requirement — retry won't help)
    - SPLIT_RECOMMENDED (oversized requirement — retry won't help)
    - Domain contamination (context issue, not output quality)
    """
    issues = evaluation.get("issues", [])
    if not issues:
        return False

    fixable_patterns = (
        "acceptance criteria",
        "given / when / then",
        "given/when/then",
        "actionable",
        "tasks must",
        "definition of done",
        "story points",
        "fibonacci",
        "placeholder",
        "user stories",
        "concrete actions",
        "planner quality gate",
    )

    return any(
        any(pattern in issue.lower() for pattern in fixable_patterns)
        for issue in issues
    )



# ═══════════════════════════════════════════════════════════════
#  GRAPH BUILDER — compile the StateGraph
# ═══════════════════════════════════════════════════════════════

def build_pipeline_graph() -> StateGraph:
    """Build and compile the LangGraph pipeline."""
    graph = StateGraph(PipelineState)

    # Register nodes
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("merge_context", merge_context_node)
    graph.add_node("planner", planner_node)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("needs_context", needs_context_node)
    graph.add_node("finalize_approved", finalize_approved_node)
    graph.add_node("finalize_revision", finalize_revision_node)
    graph.add_node("finalize_clarification", finalize_clarification_node)

    # Sequential Entry to avoid local LLM lock contention (Ollama)
    graph.add_edge(START, "analyzer")
    graph.add_edge("analyzer", "researcher")
    graph.add_edge("researcher", "merge_context")

    # Conditional: after merge_context
    graph.add_conditional_edges("merge_context", after_researcher, {
        "planner": "planner",
        "needs_context": "needs_context",
    })

    # Conditional: after planner
    graph.add_conditional_edges("planner", after_planner, {
        "evaluator": "evaluator",
        "researcher": "researcher",
        "finalize_revision": "finalize_revision",
        "finalize_clarification": "finalize_clarification",
    })

    # Conditional: after evaluator
    graph.add_conditional_edges("evaluator", after_evaluator, {
        "finalize_approved": "finalize_approved",
        "researcher": "researcher",
        "finalize_revision": "finalize_revision",
        "finalize_clarification": "finalize_clarification",
    })

    # Terminal edges
    graph.add_edge("needs_context", END)
    graph.add_edge("finalize_approved", END)
    graph.add_edge("finalize_revision", END)
    graph.add_edge("finalize_clarification", END)

    return graph.compile()


# ═══════════════════════════════════════════════════════════════
#  PUBLIC API — single entry point
# ═══════════════════════════════════════════════════════════════

# Compile once at module level
_compiled_graph = None


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_pipeline_graph()
    return _compiled_graph


def run_graph_pipeline(
    *,
    requirement: str,
    n_results: int = 5,
    allow_fallback_without_context: bool = False,
    forced_context_docs: list[str] | None = None,
    progress_callback=None,
    project_id: str | None = None,
) -> dict[str, Any]:
    """Run the full multi-agent pipeline via LangGraph.

    Returns the same dict shape as the old ScrumMasterCrew.run():
        {"context", "story", "evaluation", "actions", "next_steps"}
    """
    initial_state: PipelineState = {
        "requirement": requirement,
        "n_results": n_results,
        "allow_fallback_without_context": allow_fallback_without_context,
        "forced_context_docs": forced_context_docs,
        "project_id": project_id,
        "progress_callback": progress_callback,
        "iteration": 0,
        "max_retries": 2,
        "research_feedback": None,
        "route": {},
        "requirement_type": "software_feature",
        "tech_classification": {},
        "raw_context": {},
        "context": {},
        "story": None,
        "evaluation": None,
        "planner_quality": None,
        "actions": {},
        "next_steps": [],
    }

    logger.info("LangGraph pipeline started requirement_length=%s project_id=%s", len(requirement), project_id)

    graph = _get_graph()
    final_state = graph.invoke(initial_state)

    logger.info(
        "LangGraph pipeline completed iterations=%s status=%s",
        final_state.get("iteration", 0),
        (final_state.get("evaluation") or {}).get("status", "UNKNOWN"),
    )

    # Return the same dict shape the rest of the system expects
    return {
        "context": final_state.get("context", {}),
        "story": final_state.get("story"),
        "evaluation": final_state.get("evaluation"),
        "actions": final_state.get("actions", blocked_actions()),
        "next_steps": final_state.get("next_steps", []),
    }
