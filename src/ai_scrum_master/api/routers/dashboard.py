from fastapi import APIRouter
from typing import Any, Optional
from ai_scrum_master.core.utils.database import DatabaseManager
from ai_scrum_master.worker.celery_app import celery_app
from ai_scrum_master.actions.jira import JiraTool
from datetime import datetime, timezone
import math

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

def get_real_metrics(project_id: Optional[str] = None):
    history_col = DatabaseManager.get_history_collection()
    
    query = {"jira_key": {"$ne": "", "$exists": True}}
    if project_id:
        query["project_id"] = project_id
        
    total_tickets = history_col.count_documents(query)
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": None, 
            "avg_confidence": {"$avg": "$result.context.confidence"},
            "total_pts": {"$sum": "$story.story_points"}
        }}
    ]
    agg_result = list(history_col.aggregate(pipeline))
    avg_confidence = 0.0
    total_velocity = 0
    if agg_result:
        avg_confidence = agg_result[0].get("avg_confidence") or 0.0
        total_velocity = agg_result[0].get("total_pts") or 0
        
    confidence_percentage = round(avg_confidence * 100, 1)

    return {
        "total_tickets": total_tickets,
        "confidence_percentage": confidence_percentage,
        "total_velocity": total_velocity
    }

@router.get("/management", response_model=dict[str, Any])
def get_management_dashboard(project_id: Optional[str] = None):
    history_col = DatabaseManager.get_history_collection()
    metrics = get_real_metrics(project_id)

    # ── Try to fetch REAL data directly from Jira ──
    sprint_name = "No Active Sprint"
    sprint_end_date = "--"
    sprint_progress = 0
    active_sprint_tickets = []
    total_sprint_points = 0
    done_sprint_points = 0
    status_breakdown = {"todo": 0, "in_progress": 0, "done": 0}
    jira_connected = False

    if project_id:
        try:
            jira = JiraTool.from_project(project_id)
            if jira.config.is_configured and jira.config.board_id:
                sprint_details = jira.get_active_sprint_details(jira.config.board_id)
                if sprint_details:
                    jira_connected = True
                    sprint_name = sprint_details["name"]
                    sprint_end_date = sprint_details["end_date"]
                    sprint_progress = sprint_details["progress"]
                    total_sprint_points = sprint_details["total_points"]
                    done_sprint_points = sprint_details["done_points"]
                    status_breakdown = sprint_details["status_breakdown"]

                    # Build ticket list from real Jira issues
                    for issue in sprint_details["issues"]:
                        # Skip sub-tasks in the table to avoid clutter
                        if issue.get("issue_type", "").lower() in ("sub-task", "subtask"):
                            continue
                        active_sprint_tickets.append({
                            "key": issue["key"],
                            "title": f"[{issue['key']}] {issue['title']}",
                            "agents": ["R", "P", "E"],
                            "priority": issue["priority"],
                            "status": issue["status"],
                            "status_category": issue.get("status_category", ""),
                            "story_points": issue.get("story_points", 0),
                        })
        except Exception as e:
            import traceback
            traceback.print_exc()

    # ── Fallback: use MongoDB history if Jira did not return tickets ──
    if not active_sprint_tickets:
        query = {"jira_key": {"$ne": "", "$exists": True}}
        if project_id:
            query["project_id"] = project_id

        recent_tickets_cursor = history_col.find(query).sort("created_at", -1).limit(10)
        for t in recent_tickets_cursor:
            story = t.get("story", {})
            jira_key = t.get("jira_key", "")
            title = story.get("title", "Untitled Requirement")
            priority = story.get("priority", "MEDIUM")
            if not priority:
                priority = "MEDIUM"
            active_sprint_tickets.append({
                "key": jira_key,
                "title": f"[{jira_key}] {title}",
                "agents": ["R", "P", "E"],
                "priority": priority.upper(),
                "status": "In Progress",
                "status_category": "indeterminate",
                "story_points": story.get("story_points", 0),
            })

    # ── Ping Celery workers to check Agent health ──
    i = celery_app.control.ping(timeout=0.5)
    worker_status = "Active" if i else "Offline"

    # ── Compute Team Velocity (combine Jira done points with historical data) ──
    team_velocity = metrics["total_velocity"]
    if jira_connected and done_sprint_points > 0:
        team_velocity = max(team_velocity, int(done_sprint_points))

    # ── Build burndown data from status breakdown ──
    burndown_data = []
    total_issues_count = sum(status_breakdown.values())
    if total_issues_count > 0:
        burndown_data = [
            {"label": "To Do", "count": status_breakdown["todo"]},
            {"label": "In Progress", "count": status_breakdown["in_progress"]},
            {"label": "Done", "count": status_breakdown["done"]},
        ]

    # ── Build AI insight text ──
    if jira_connected:
        insight = (
            f"Sprint '{sprint_name}': {status_breakdown['done']}/{total_issues_count} tickets Done "
            f"({sprint_progress}%). "
            f"Tổng {done_sprint_points:.0f}/{total_sprint_points:.0f} Story Points đã hoàn thành."
        )
    else:
        insight = (
            f"Hệ thống đã phân tích và đẩy thành công {metrics['total_tickets']} tickets "
            f"lên Jira với độ chính xác {metrics['confidence_percentage']}%."
        )

    return {
        "sprintName": sprint_name,
        "sprintEndDate": sprint_end_date,
        "sprintProgress": sprint_progress,
        "totalTickets": metrics["total_tickets"] if not jira_connected else max(metrics["total_tickets"], total_issues_count),
        "totalTicketsTrend": "Real data only" if not jira_connected else f"{status_breakdown['done']} Done / {status_breakdown['in_progress']} In Progress / {status_breakdown['todo']} To Do",
        "aiConfidenceScore": metrics["confidence_percentage"],
        "teamVelocity": team_velocity,
        "activeSprintTickets": active_sprint_tickets,
        "agentInsight": insight,
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

@router.get("/analytics", response_model=dict[str, Any])
def get_analytics_overview(project_id: Optional[str] = None):
    projects = DatabaseManager.get_all_projects()
    history_col = DatabaseManager.get_history_collection()
    metrics = get_real_metrics(project_id)

    if project_id:
        projects = [p for p in projects if str(p.get("id", "")) == project_id or str(p.get("_id", "")) == project_id]

    tv_details = []
    resource_efficiency = []
    total_all_pts = 0
    jira_connected = False

    # ── Per-project: try real Jira sprint data, fallback to MongoDB ──
    sprint_status_breakdown = {"todo": 0, "in_progress": 0, "done": 0}
    sprint_total_points = 0.0
    sprint_done_points = 0.0
    sprint_total_issues = 0

    for p in projects:
        p_id = str(p.get("id", p.get("_id", "")))
        p_name = p.get("name", "Unknown")

        p_velocity = 0
        p_done = 0
        p_in_progress = 0
        p_todo = 0
        p_total_issues = 0
        p_total_pts = 0.0
        p_done_pts = 0.0
        p_jira_ok = False

        # Try Jira first
        try:
            jira = JiraTool.from_project(p_id)
            if jira.config.is_configured and jira.config.board_id:
                sprint_details = jira.get_active_sprint_details(jira.config.board_id)
                if sprint_details and sprint_details["total_issues"] > 0:
                    p_jira_ok = True
                    jira_connected = True
                    p_total_pts = sprint_details["total_points"]
                    p_done_pts = sprint_details["done_points"]
                    p_velocity = int(p_done_pts) if p_done_pts > 0 else 0
                    sb = sprint_details["status_breakdown"]
                    p_done = sb["done"]
                    p_in_progress = sb["in_progress"]
                    p_todo = sb["todo"]
                    p_total_issues = sprint_details["total_issues"]

                    sprint_status_breakdown["todo"] += p_todo
                    sprint_status_breakdown["in_progress"] += p_in_progress
                    sprint_status_breakdown["done"] += p_done
                    sprint_total_points += p_total_pts
                    sprint_done_points += p_done_pts
                    sprint_total_issues += p_total_issues
        except Exception:
            pass

        # Fallback to MongoDB history velocity
        if not p_jira_ok:
            pipeline = [
                {"$match": {"project_id": p_id, "jira_key": {"$ne": "", "$exists": True}}},
                {"$group": {"_id": None, "total_pts": {"$sum": "$story.story_points"}}}
            ]
            agg_result = list(history_col.aggregate(pipeline))
            p_velocity = agg_result[0].get("total_pts") or 0 if agg_result else 0

        total_all_pts += p_velocity

        if p_velocity > 0 or p_jira_ok:
            tv_details.append({
                "name": p_name,
                "pts": p_velocity,
                "done_pts": p_done_pts,
                "total_pts": p_total_pts,
            })

        # Compute blocker ratio: tickets stuck in To Do relative to total
        blocker_ratio = 0
        if p_total_issues > 0:
            blocker_ratio = round((p_todo / p_total_issues) * 100)

        # Compute cycle time approximation from Jira
        # If we have done tickets with story points, we can approximate
        cycle_time = "N/A"
        if p_jira_ok and p_done > 0:
            cycle_time = f"~{p_done} done"

        resource_efficiency.append({
            "name": p_name,
            "cycleTime": cycle_time,
            "blockerRatio": blocker_ratio,
            "aiAutomation": "100% SYNC" if p_jira_ok else "OFFLINE",
            "trend": "up" if p_velocity > 0 else "flat",
            "done": p_done,
            "in_progress": p_in_progress,
            "todo": p_todo,
        })

    avg_vel = total_all_pts / len(projects) if projects else 0

    # ── Calculate Lead Time from MongoDB history (Jira doesn't store AI creation timestamp) ──
    query = {"jira_key": {"$ne": "", "$exists": True}}
    if project_id:
        query["project_id"] = project_id

    all_tickets = list(history_col.find(query))
    now = datetime.now(timezone.utc)
    lead_times = {"1d": 0, "2d": 0, "3d": 0, "5d+": 0}
    for t in all_tickets:
        try:
            created_at = datetime.fromisoformat(t.get("created_at").replace("Z", "+00:00"))
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
    lead_time_data = {
        "1d": {"count": lead_times["1d"], "percentage": (lead_times["1d"]/total_lead*100) if total_lead else 0},
        "2d": {"count": lead_times["2d"], "percentage": (lead_times["2d"]/total_lead*100) if total_lead else 0},
        "3d": {"count": lead_times["3d"], "percentage": (lead_times["3d"]/total_lead*100) if total_lead else 0},
        "5d": {"count": lead_times["5d+"], "percentage": (lead_times["5d+"]/total_lead*100) if total_lead else 0},
    }

    # ── Build real burndown SVG path from sprint status breakdown ──
    if sprint_total_issues > 0:
        # Compute actual burndown: remaining = total - done, mid = total - done - (in_progress * 0.5)
        remaining_pct = ((sprint_total_issues - sprint_status_breakdown["done"]) / sprint_total_issues) * 100
        mid_pct = ((sprint_total_issues - sprint_status_breakdown["done"] - sprint_status_breakdown["in_progress"] * 0.5) / sprint_total_issues) * 100
        # SVG path: Y=0 is top (remaining=100%), Y=100% is bottom (remaining=0%)
        # Map: start at remaining=100% (y=0), mid point, end at current remaining
        start_y = 0   # start of sprint = 100% remaining → top
        mid_y = int(100 - mid_pct)
        end_y = int(100 - remaining_pct)
        active_burndown_path = f"M0,{start_y} Q50,{mid_y} 100,{end_y}"
    else:
        active_burndown_path = "M0,0 L100,100"

    # ── Build AI insight from real data ──
    if jira_connected:
        ai_insight = (
            f"Phân tích Sprint thực tế: {sprint_status_breakdown['done']}/{sprint_total_issues} tickets Done "
            f"({sprint_done_points:.0f}/{sprint_total_points:.0f} SP). "
        )
        if sprint_total_points > 0:
            pct = int((sprint_done_points / sprint_total_points) * 100)
            if pct >= 80:
                ai_insight += "Tiến độ tốt, sprint có khả năng hoàn thành đúng hạn."
            elif pct >= 50:
                ai_insight += "Cần đẩy nhanh các ticket còn lại để đảm bảo deadline."
            else:
                ai_insight += "Tiến độ chậm, cần review lại scope sprint."
        if metrics["confidence_percentage"] > 0:
            ai_insight += f" AI Confidence: {metrics['confidence_percentage']}%."
    else:
        ai_insight = f"Phân tích dữ liệu thực tế: Hệ thống ghi nhận {metrics['total_tickets']} tickets. "
        if metrics["confidence_percentage"] > 90:
            ai_insight += "Độ chính xác hiện tại rất cao, gợi ý tiếp tục duy trì."
        else:
            ai_insight += "Độ chính xác cần cải thiện."

    return {
        "accuracy": metrics["confidence_percentage"],
        "accuracyTrend": "Real data only" if not jira_connected else f"{sprint_done_points:.0f}/{sprint_total_points:.0f} SP done",
        "teamVelocityDetails": tv_details,
        "averageVelocity": round(avg_vel, 1),
        "resourceEfficiency": resource_efficiency,
        "leadTimeData": lead_time_data,
        "activeBurndownPath": active_burndown_path,
        "aiInsightText": ai_insight,
        "jiraConnected": jira_connected,
        "statusBreakdown": sprint_status_breakdown,
        "totalSprintPoints": sprint_total_points,
        "doneSprintPoints": sprint_done_points,
        "totalSprintIssues": sprint_total_issues,
    }

@router.get("/team", response_model=dict[str, Any])
def get_team_members(project_id: Optional[str] = None):
    metrics = get_real_metrics(project_id)
    
    # Active nodes based on celery workers
    i = celery_app.control.ping(timeout=0.5)
    active_nodes = []
    if i:
        for worker_node in i:
            for worker_name, response in worker_node.items():
                if response.get("ok") == "pong":
                    active_nodes.append({
                        "name": f"Celery Worker ({worker_name})",
                        "task": "Listening for tasks...",
                        "status": "active"
                    })

    return {
        "agentEfficiency": metrics["confidence_percentage"],
        "agentVelocityAudit": f"Autonomous agents have processed {metrics['total_tickets']} Jira tickets.",
        "activeAgentNodes": active_nodes,
        "members": [], # Trống vì không có DB quản lý User
        "teamSeats": { "used": 0, "total": 0 },
        "aiAgentTokens": len(active_nodes),
        "pendingInvites": 0
    }
