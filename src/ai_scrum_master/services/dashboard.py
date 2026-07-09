from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ai_scrum_master.actions.jira import JiraTool
from ai_scrum_master.core.utils.database import DatabaseManager
from ai_scrum_master.core.utils.logging import get_logger
from ai_scrum_master.worker.celery_app import celery_app

logger = get_logger(__name__)


class DashboardService:
    def get_real_metrics(self, project_id: str | None = None) -> dict[str, Any]:
        history_col = DatabaseManager.get_history_collection()
        query = self._history_query(project_id)

        total_tickets = history_col.count_documents(query)
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": None,
                    "avg_confidence": {"$avg": "$result.context.confidence"},
                    "total_pts": {"$sum": "$story.story_points"},
                }
            },
        ]
        agg_result = list(history_col.aggregate(pipeline))
        avg_confidence = 0.0
        total_velocity = 0
        if agg_result:
            avg_confidence = agg_result[0].get("avg_confidence") or 0.0
            total_velocity = agg_result[0].get("total_pts") or 0

        return {
            "total_tickets": total_tickets,
            "confidence_percentage": round(avg_confidence * 100, 1),
            "total_velocity": total_velocity,
        }

    def get_management_dashboard(self, project_id: str | None = None) -> dict[str, Any]:
        history_col = DatabaseManager.get_history_collection()
        metrics = self.get_real_metrics(project_id)

        sprint_name = "No Active Sprint"
        sprint_end_date = "--"
        sprint_progress = 0
        active_sprint_tickets: list[dict[str, Any]] = []
        total_sprint_points = 0.0
        done_sprint_points = 0.0
        status_breakdown = {"todo": 0, "in_progress": 0, "done": 0}
        jira_connected = False

        sprint_details = self._load_active_sprint_details(project_id)
        if sprint_details:
            jira_connected = True
            sprint_name = sprint_details["name"]
            sprint_end_date = sprint_details["end_date"]
            sprint_progress = sprint_details["progress"]
            total_sprint_points = sprint_details["total_points"]
            done_sprint_points = sprint_details["done_points"]
            status_breakdown = sprint_details["status_breakdown"]
            active_sprint_tickets = self._build_active_sprint_tickets(sprint_details["issues"])

        if not active_sprint_tickets:
            active_sprint_tickets = self._build_recent_history_tickets(history_col, project_id)

        worker_status = self._worker_status_label()
        total_issues_count = sum(status_breakdown.values())
        team_velocity = metrics["total_velocity"]
        if jira_connected and done_sprint_points > 0:
            team_velocity = max(team_velocity, int(done_sprint_points))

        burndown_data = []
        if total_issues_count > 0:
            burndown_data = [
                {"label": "To Do", "count": status_breakdown["todo"]},
                {"label": "In Progress", "count": status_breakdown["in_progress"]},
                {"label": "Done", "count": status_breakdown["done"]},
            ]

        return {
            "sprintName": sprint_name,
            "sprintEndDate": sprint_end_date,
            "sprintProgress": sprint_progress,
            "totalTickets": metrics["total_tickets"] if not jira_connected else max(metrics["total_tickets"], total_issues_count),
            "totalTicketsTrend": (
                "Real data only"
                if not jira_connected
                else f"{status_breakdown['done']} Done / {status_breakdown['in_progress']} In Progress / {status_breakdown['todo']} To Do"
            ),
            "aiConfidenceScore": metrics["confidence_percentage"],
            "teamVelocity": team_velocity,
            "activeSprintTickets": active_sprint_tickets,
            "agentInsight": self._build_management_insight(
                jira_connected=jira_connected,
                sprint_name=sprint_name,
                sprint_progress=sprint_progress,
                status_breakdown=status_breakdown,
                total_issues_count=total_issues_count,
                done_sprint_points=done_sprint_points,
                total_sprint_points=total_sprint_points,
                total_tickets=metrics["total_tickets"],
                confidence_percentage=metrics["confidence_percentage"],
            ),
            "agentHealth": {
                "researcher": worker_status,
                "planner": worker_status,
                "evaluator": worker_status,
            },
            "statusBreakdown": status_breakdown,
            "burndownData": burndown_data,
            "jiraConnected": jira_connected,
            "totalSprintPoints": total_sprint_points,
            "doneSprintPoints": done_sprint_points,
        }

    def get_analytics_overview(self, project_id: str | None = None) -> dict[str, Any]:
        projects = DatabaseManager.get_all_projects()
        history_col = DatabaseManager.get_history_collection()
        metrics = self.get_real_metrics(project_id)

        if project_id:
            projects = [p for p in projects if str(p.get("id", "")) == project_id or str(p.get("_id", "")) == project_id]

        tv_details = []
        resource_efficiency = []
        total_all_pts = 0
        jira_connected = False

        sprint_status_breakdown = {"todo": 0, "in_progress": 0, "done": 0}
        sprint_total_points = 0.0
        sprint_done_points = 0.0
        sprint_total_issues = 0

        for project in projects:
            project_summary = self._build_project_analytics_summary(project, history_col)
            jira_connected = jira_connected or project_summary["jira_connected"]
            total_all_pts += project_summary["velocity"]

            if project_summary["velocity"] > 0 or project_summary["jira_connected"]:
                tv_details.append(
                    {
                        "name": project_summary["name"],
                        "pts": project_summary["velocity"],
                        "done_pts": project_summary["done_pts"],
                        "total_pts": project_summary["total_pts"],
                    }
                )

            resource_efficiency.append(
                {
                    "name": project_summary["name"],
                    "cycleTime": project_summary["cycle_time"],
                    "blockerRatio": project_summary["blocker_ratio"],
                    "aiAutomation": "100% SYNC" if project_summary["jira_connected"] else "OFFLINE",
                    "trend": "up" if project_summary["velocity"] > 0 else "flat",
                    "done": project_summary["done"],
                    "in_progress": project_summary["in_progress"],
                    "todo": project_summary["todo"],
                }
            )

            sprint_status_breakdown["todo"] += project_summary["todo"]
            sprint_status_breakdown["in_progress"] += project_summary["in_progress"]
            sprint_status_breakdown["done"] += project_summary["done"]
            sprint_total_points += project_summary["total_pts"]
            sprint_done_points += project_summary["done_pts"]
            sprint_total_issues += project_summary["total_issues"]

        avg_vel = total_all_pts / len(projects) if projects else 0
        lead_time_data = self._build_lead_time_data(history_col, project_id)
        active_burndown_path = self._build_burndown_path(
            sprint_total_issues=sprint_total_issues,
            status_breakdown=sprint_status_breakdown,
        )

        return {
            "accuracy": metrics["confidence_percentage"],
            "accuracyTrend": "Real data only" if not jira_connected else f"{sprint_done_points:.0f}/{sprint_total_points:.0f} SP done",
            "teamVelocityDetails": tv_details,
            "averageVelocity": round(avg_vel, 1),
            "resourceEfficiency": resource_efficiency,
            "leadTimeData": lead_time_data,
            "activeBurndownPath": active_burndown_path,
            "aiInsightText": self._build_analytics_insight(
                jira_connected=jira_connected,
                sprint_status_breakdown=sprint_status_breakdown,
                sprint_total_issues=sprint_total_issues,
                sprint_done_points=sprint_done_points,
                sprint_total_points=sprint_total_points,
                total_tickets=metrics["total_tickets"],
                confidence_percentage=metrics["confidence_percentage"],
            ),
            "jiraConnected": jira_connected,
            "statusBreakdown": sprint_status_breakdown,
            "totalSprintPoints": sprint_total_points,
            "doneSprintPoints": sprint_done_points,
            "totalSprintIssues": sprint_total_issues,
        }

    def get_team_members(self, project_id: str | None = None) -> dict[str, Any]:
        metrics = self.get_real_metrics(project_id)
        active_nodes = self._get_active_worker_nodes()

        return {
            "agentEfficiency": metrics["confidence_percentage"],
            "agentVelocityAudit": f"Autonomous agents have processed {metrics['total_tickets']} Jira tickets.",
            "activeAgentNodes": active_nodes,
            "members": [],
            "teamSeats": {"used": 0, "total": 0},
            "aiAgentTokens": len(active_nodes),
            "pendingInvites": 0,
        }

    def _history_query(self, project_id: str | None = None) -> dict[str, Any]:
        query: dict[str, Any] = {"jira_key": {"$ne": "", "$exists": True}}
        if project_id:
            query["project_id"] = project_id
        return query

    def _load_active_sprint_details(self, project_id: str | None) -> dict[str, Any] | None:
        if not project_id:
            return None

        try:
            jira = JiraTool.from_project(project_id)
            if jira.config.is_configured and jira.config.board_id:
                return jira.get_active_sprint_details(jira.config.board_id)
        except Exception as exc:
            logger.warning("Failed to load active sprint details for project_id=%s: %s", project_id, exc)
        return None

    def _build_active_sprint_tickets(self, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        tickets = []
        for issue in issues:
            if issue.get("issue_type", "").lower() in ("sub-task", "subtask"):
                continue
            tickets.append(
                {
                    "key": issue["key"],
                    "title": f"[{issue['key']}] {issue['title']}",
                    "agents": ["R", "P", "E"],
                    "priority": issue["priority"],
                    "status": issue["status"],
                    "status_category": issue.get("status_category", ""),
                    "story_points": issue.get("story_points", 0),
                }
            )
        return tickets

    def _build_recent_history_tickets(self, history_col: Any, project_id: str | None) -> list[dict[str, Any]]:
        tickets = []
        recent_tickets_cursor = history_col.find(self._history_query(project_id)).sort("created_at", -1).limit(10)
        for ticket in recent_tickets_cursor:
            story = ticket.get("story", {})
            jira_key = ticket.get("jira_key", "")
            priority = story.get("priority") or "MEDIUM"
            tickets.append(
                {
                    "key": jira_key,
                    "title": f"[{jira_key}] {story.get('title', 'Untitled Requirement')}",
                    "agents": ["R", "P", "E"],
                    "priority": priority.upper(),
                    "status": "In Progress",
                    "status_category": "indeterminate",
                    "story_points": story.get("story_points", 0),
                }
            )
        return tickets

    def _worker_status_label(self) -> str:
        return "Active" if celery_app.control.ping(timeout=0.5) else "Offline"

    def _get_active_worker_nodes(self) -> list[dict[str, Any]]:
        nodes = []
        ping_result = celery_app.control.ping(timeout=0.5)
        if not ping_result:
            return nodes

        for worker_node in ping_result:
            for worker_name, response in worker_node.items():
                if response.get("ok") == "pong":
                    nodes.append(
                        {
                            "name": f"Celery Worker ({worker_name})",
                            "task": "Listening for tasks...",
                            "status": "active",
                        }
                    )
        return nodes

    def _build_management_insight(
        self,
        *,
        jira_connected: bool,
        sprint_name: str,
        sprint_progress: int,
        status_breakdown: dict[str, int],
        total_issues_count: int,
        done_sprint_points: float,
        total_sprint_points: float,
        total_tickets: int,
        confidence_percentage: float,
    ) -> str:
        if jira_connected:
            return (
                f"Sprint '{sprint_name}': {status_breakdown['done']}/{total_issues_count} tickets Done "
                f"({sprint_progress}%). Completed {done_sprint_points:.0f}/{total_sprint_points:.0f} Story Points."
            )
        return (
            f"PM Agent has analyzed and prepared {total_tickets} Jira tickets "
            f"with {confidence_percentage}% confidence."
        )

    def _build_project_analytics_summary(self, project: dict[str, Any], history_col: Any) -> dict[str, Any]:
        project_id = str(project.get("id", project.get("_id", "")))
        project_name = project.get("name", "Unknown")

        velocity = 0
        done = 0
        in_progress = 0
        todo = 0
        total_issues = 0
        total_pts = 0.0
        done_pts = 0.0
        jira_ok = False

        try:
            jira = JiraTool.from_project(project_id)
            if jira.config.is_configured and jira.config.board_id:
                sprint_details = jira.get_active_sprint_details(jira.config.board_id)
                if sprint_details and sprint_details["total_issues"] > 0:
                    jira_ok = True
                    total_pts = sprint_details["total_points"]
                    done_pts = sprint_details["done_points"]
                    velocity = int(done_pts) if done_pts > 0 else 0
                    status_breakdown = sprint_details["status_breakdown"]
                    done = status_breakdown["done"]
                    in_progress = status_breakdown["in_progress"]
                    todo = status_breakdown["todo"]
                    total_issues = sprint_details["total_issues"]
        except Exception as exc:
            logger.warning("Failed to load project analytics from Jira project_id=%s: %s", project_id, exc)

        if not jira_ok:
            pipeline = [
                {"$match": {"project_id": project_id, "jira_key": {"$ne": "", "$exists": True}}},
                {"$group": {"_id": None, "total_pts": {"$sum": "$story.story_points"}}},
            ]
            agg_result = list(history_col.aggregate(pipeline))
            velocity = agg_result[0].get("total_pts") or 0 if agg_result else 0

        blocker_ratio = round((todo / total_issues) * 100) if total_issues > 0 else 0
        cycle_time = f"~{done} done" if jira_ok and done > 0 else "N/A"

        return {
            "name": project_name,
            "velocity": velocity,
            "done": done,
            "in_progress": in_progress,
            "todo": todo,
            "total_issues": total_issues,
            "total_pts": total_pts,
            "done_pts": done_pts,
            "jira_connected": jira_ok,
            "blocker_ratio": blocker_ratio,
            "cycle_time": cycle_time,
        }

    def _build_lead_time_data(self, history_col: Any, project_id: str | None) -> dict[str, Any]:
        all_tickets = list(history_col.find(self._history_query(project_id)))
        now = datetime.now(timezone.utc)
        lead_times = {"1d": 0, "2d": 0, "3d": 0, "5d+": 0}
        for ticket in all_tickets:
            try:
                created_at = datetime.fromisoformat(ticket.get("created_at").replace("Z", "+00:00"))
                days = (now - created_at).days
                if days <= 1:
                    lead_times["1d"] += 1
                elif days == 2:
                    lead_times["2d"] += 1
                elif days <= 4:
                    lead_times["3d"] += 1
                else:
                    lead_times["5d+"] += 1
            except Exception:
                lead_times["5d+"] += 1

        total_lead = sum(lead_times.values())
        return {
            "1d": {"count": lead_times["1d"], "percentage": (lead_times["1d"] / total_lead * 100) if total_lead else 0},
            "2d": {"count": lead_times["2d"], "percentage": (lead_times["2d"] / total_lead * 100) if total_lead else 0},
            "3d": {"count": lead_times["3d"], "percentage": (lead_times["3d"] / total_lead * 100) if total_lead else 0},
            "5d": {"count": lead_times["5d+"], "percentage": (lead_times["5d+"] / total_lead * 100) if total_lead else 0},
        }

    def _build_burndown_path(self, *, sprint_total_issues: int, status_breakdown: dict[str, int]) -> str:
        if sprint_total_issues <= 0:
            return "M0,0 L100,100"

        remaining_pct = ((sprint_total_issues - status_breakdown["done"]) / sprint_total_issues) * 100
        mid_pct = ((sprint_total_issues - status_breakdown["done"] - status_breakdown["in_progress"] * 0.5) / sprint_total_issues) * 100
        start_y = 0
        mid_y = int(100 - mid_pct)
        end_y = int(100 - remaining_pct)
        return f"M0,{start_y} Q50,{mid_y} 100,{end_y}"

    def _build_analytics_insight(
        self,
        *,
        jira_connected: bool,
        sprint_status_breakdown: dict[str, int],
        sprint_total_issues: int,
        sprint_done_points: float,
        sprint_total_points: float,
        total_tickets: int,
        confidence_percentage: float,
    ) -> str:
        if jira_connected:
            insight = (
                f"Live sprint analysis: {sprint_status_breakdown['done']}/{sprint_total_issues} tickets Done "
                f"({sprint_done_points:.0f}/{sprint_total_points:.0f} SP). "
            )
            if sprint_total_points > 0:
                pct = int((sprint_done_points / sprint_total_points) * 100)
                if pct >= 80:
                    insight += "Progress is strong and the sprint is likely to finish on time."
                elif pct >= 50:
                    insight += "Remaining tickets should be accelerated to protect the deadline."
                else:
                    insight += "Progress is slow; review sprint scope and blockers."
            if confidence_percentage > 0:
                insight += f" AI Confidence: {confidence_percentage}%."
            return insight

        insight = f"Real data analysis: PM Agent has recorded {total_tickets} tickets. "
        if confidence_percentage > 90:
            insight += "Current confidence is very high; keep the workflow steady."
        else:
            insight += "Confidence needs improvement; review input quality and context coverage."
        return insight
