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
from ai_scrum_master.agents.tech_classifier import TechClassifierAgent
from ai_scrum_master.core.config.settings import get_runtime_profiles
from ai_scrum_master.core.pipeline.context_selector import select_context_for_route
from ai_scrum_master.core.pipeline.finalizer import blocked_actions, finalize_generation, should_block_planning
from ai_scrum_master.workflows.graph_state import PipelineState
from ai_scrum_master.core.utils.logging import get_logger
from ai_scrum_master.core.validation.quality import AMBIGUOUS_REQUEST, OVERSIZED_REQUEST, classify_requirement, validate_story_against_requirement
from ai_scrum_master.core.pipeline.requirement_router import route_requirement
from ai_scrum_master.core.validation.story_validator import evaluate_planner_output, validate_post_generation

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
#  NODES — each receives full state, returns only changed keys
# ═══════════════════════════════════════════════════════════════

def route_requirement_node(state: PipelineState) -> dict[str, Any]:
    """Classify requirement domain and determine routing profile."""
    route = route_requirement(state["requirement"])
    requirement_type = route.get("story_type") or classify_requirement(state["requirement"])
    logger.info("Graph node [route_requirement] domain=%s type=%s", route.get("domain"), requirement_type)
    return {"route": route, "requirement_type": requirement_type}


def tech_classifier_node(state: PipelineState) -> dict[str, Any]:
    """Run TechClassifierAgent to extract tech_stack and domain."""
    classifier = TechClassifierAgent()
    logger.info("Graph node [tech_classifier] starting")
    classification = classifier.run(state["requirement"], state.get("route", {}))
    return {"tech_classification": classification}


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
    planner_quality = evaluate_planner_output(state["requirement"], story, state["context"])
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
    validation_issues = validate_story_against_requirement(state["requirement"], story)
    if validation_issues:
        logger.info("Post-generation validation failed issues=%s", len(validation_issues))
        req_type = state.get("requirement_type", "software_feature")
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


# ═══════════════════════════════════════════════════════════════
#  CONDITIONAL EDGES — router functions that pick the next node
# ═══════════════════════════════════════════════════════════════

def after_researcher(state: PipelineState) -> Literal["planner", "needs_context"]:
    """After researcher: check if context is sufficient to proceed."""
    if should_block_planning(state["context"], state.get("allow_fallback_without_context", False)):
        return "needs_context"
    return "planner"


def after_planner(state: PipelineState) -> Literal["evaluator", "researcher", "finalize_revision"]:
    """After planner: check deterministic quality gate."""
    pq = state.get("planner_quality", {})
    if pq.get("passed", True):
        return "evaluator"

    # Quality gate failed — retry or give up
    if state.get("iteration", 1) <= state.get("max_retries", 2):
        logger.info("Graph router [after_planner] quality gate failed, retrying researcher")
        return "researcher"

    logger.info("Graph router [after_planner] quality gate failed, no retries left")
    return "finalize_revision"


def after_evaluator(state: PipelineState) -> Literal["finalize_approved", "researcher", "finalize_revision"]:
    """After evaluator: route based on evaluation status."""
    evaluation = state.get("evaluation") or {}
    status = evaluation.get("status", "REVISION")

    if status == "APPROVED":
        return "finalize_approved"

    # REVISION or any non-approved status — retry or give up
    if state.get("iteration", 1) <= state.get("max_retries", 2):
        logger.info("Graph router [after_evaluator] REVISION, retrying. feedback=%s", str(state.get("research_feedback", ""))[:100])
        return "researcher"

    logger.info("Graph router [after_evaluator] REVISION, no retries left")
    return "finalize_revision"


# ═══════════════════════════════════════════════════════════════
#  GRAPH BUILDER — compile the StateGraph
# ═══════════════════════════════════════════════════════════════

def build_pipeline_graph() -> StateGraph:
    """Build and compile the LangGraph pipeline."""
    graph = StateGraph(PipelineState)

    # Register nodes
    graph.add_node("route_requirement", route_requirement_node)
    graph.add_node("tech_classifier", tech_classifier_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("merge_context", merge_context_node)
    graph.add_node("planner", planner_node)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("needs_context", needs_context_node)
    graph.add_node("finalize_approved", finalize_approved_node)
    graph.add_node("finalize_revision", finalize_revision_node)

    # Parallel Entry
    graph.add_edge(START, "route_requirement")
    graph.add_edge(START, "researcher")
    graph.add_edge(START, "tech_classifier")

    # Fan-in
    # Note: route_requirement has no explicit outgoing edge, meaning its branch terminates after it runs.
    # However, since researcher runs in parallel and points to merge_context, the next super-step (merge_context)
    # will only run after ALL parallel branches finish, and will only be scheduled ONCE.
    graph.add_edge("researcher", "merge_context")
    graph.add_edge("tech_classifier", "merge_context")

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
    })

    # Conditional: after evaluator
    graph.add_conditional_edges("evaluator", after_evaluator, {
        "finalize_approved": "finalize_approved",
        "researcher": "researcher",
        "finalize_revision": "finalize_revision",
    })

    # Terminal edges
    graph.add_edge("needs_context", END)
    graph.add_edge("finalize_approved", END)
    graph.add_edge("finalize_revision", END)

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
