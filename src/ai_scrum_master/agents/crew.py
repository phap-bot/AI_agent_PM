from __future__ import annotations

from ai_scrum_master.agents.evaluator import EvaluatorAgent
from ai_scrum_master.agents.planner import PlannerAgent
from ai_scrum_master.agents.researcher import ResearcherAgent
from ai_scrum_master.agents.tools.jira_tool import JiraTool
from ai_scrum_master.agents.tools.slack_tool import SlackTool
from ai_scrum_master.core.config import get_runtime_profiles
from ai_scrum_master.core.logging import get_logger

logger = get_logger(__name__)


class ScrumMasterCrew:
    def __init__(self) -> None:
        profiles = get_runtime_profiles()
        self.researcher = ResearcherAgent(profile=profiles.agents.get("researcher"))
        self.planner = PlannerAgent(profile=profiles.agents.get("planner"))
        self.evaluator = EvaluatorAgent(profile=profiles.agents.get("evaluator"))
        self.jira_tool = JiraTool()
        self.slack_tool = SlackTool()
        self.task_profiles = profiles.tasks

    def run(self, requirement: str, n_results: int = 5) -> dict:
        logger.info("Pipeline started requirement_length=%s n_results=%s", len(requirement), n_results)
        logger.info("Researcher stage started")
        context = self.researcher.run(requirement=requirement, n_results=n_results)
        logger.info(
            "Researcher stage completed documents=%s confidence=%s warnings=%s",
            len(context.get("documents", [])),
            context.get("confidence"),
            len(context.get("warnings", [])),
        )

        logger.info("Planner stage started")
        story = self.planner.run(requirement=requirement, context=context)
        logger.info(
            "Planner stage completed title=%s planning_status=%s warnings=%s",
            story.get("title"),
            story.get("planning_status", "READY"),
            len(story.get("warnings", [])),
        )

        logger.info("Evaluator stage started")
        evaluation = self.evaluator.run(story=story)
        logger.info(
            "Evaluator stage completed status=%s issues=%s warnings=%s",
            evaluation.get("status"),
            len(evaluation.get("issues", [])),
            len(evaluation.get("warnings", [])),
        )

        actions = self._prepare_actions(story, evaluation)
        logger.info("Pipeline completed action_ready jira=%s slack=%s", actions["jira"]["ready"], actions["slack"]["ready"])
        return {
            "context": context,
            "story": story,
            "evaluation": evaluation,
            "actions": actions,
        }

    def _prepare_actions(self, story: dict, evaluation: dict) -> dict:
        if evaluation.get("status") != "APPROVED" or story.get("planning_status", "READY") != "READY":
            logger.info(
                "Action previews blocked evaluation_status=%s planning_status=%s",
                evaluation.get("status"),
                story.get("planning_status", "READY"),
            )
            warning = "Action blocked until evaluator returns APPROVED and planning_status is READY."
            return {
                "jira": {"ready": False, "payload": None, "warnings": [warning]},
                "slack": {"ready": False, "payload": None, "warnings": [warning]},
            }

        logger.info("Action previews prepared for approved ready story")
        return {
            "jira": self.jira_tool.prepare_action(story),
            "slack": self.slack_tool.prepare_action(story, evaluation),
        }
