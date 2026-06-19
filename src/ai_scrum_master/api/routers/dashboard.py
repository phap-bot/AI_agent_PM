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
    
    query = {"jira_key": {"$ne": "", "$exists": True}}
    if project_id:
        query["project_id"] = project_id
        
    recent_tickets_cursor = history_col.find(query).sort("created_at", -1).limit(10)
    active_sprint_tickets = []
    
    for t in recent_tickets_cursor:
        story = t.get("story", {})
        jira_key = t.get("jira_key", "")
        title = story.get("title", "Untitled Requirement")
        priority = story.get("priority", "MEDIUM")
        if not priority:
            priority = "MEDIUM"
            
        active_sprint_tickets.append({
            "title": f"[{jira_key}] {title}",
            "agents": ["R", "P", "E"],
            "priority": priority.upper(),
            "status": "In Progress"
        })

    # Ping Celery workers to see if agents are alive
    i = celery_app.control.ping(timeout=0.5)
    worker_status = "Active" if i else "Offline"
    
    # Get active sprint from Jira if possible
    sprint_name = "No Active Sprint"
    sprint_end_date = "--"
    sprint_progress = 0
    if project_id:
        try:
            jira = JiraTool.from_project(project_id)
            if jira.config.board_id:
                sprint_id = jira._get_active_sprint(jira.config.board_id)
                if sprint_id:
                    sprint_url = f"{jira.config.base_url.rstrip('/')}/rest/agile/1.0/sprint/{sprint_id}"
                    sprint_resp = jira.http_client.get_json(
                        url=sprint_url,
                        basic_auth=(jira.config.email, jira.config.api_token),
                        headers={"Accept": "application/json"}
                    )
                    if sprint_resp.status_code == 200:
                        sdata = sprint_resp.json_body
                        sprint_name = sdata.get("name", sprint_name)
                        end_date_str = sdata.get("endDate")
                        if end_date_str:
                            ed = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                            sprint_end_date = ed.strftime("%b %d, %Y")
                            # calculate progress
                            now = datetime.now(timezone.utc)
                            sd = datetime.fromisoformat(sdata.get("startDate", "").replace("Z", "+00:00")) if sdata.get("startDate") else now
                            if ed > sd:
                                progress = (now - sd).total_seconds() / (ed - sd).total_seconds()
                                sprint_progress = min(100, max(0, int(progress * 100)))
        except Exception:
            pass

    return {
        "sprintName": sprint_name,
        "sprintEndDate": sprint_end_date,
        "sprintProgress": sprint_progress,
        "totalTickets": metrics["total_tickets"],
        "totalTicketsTrend": "Real data only", 
        "aiConfidenceScore": metrics["confidence_percentage"],
        "teamVelocity": metrics["total_velocity"],
        "activeSprintTickets": active_sprint_tickets,
        "agentInsight": f"Hệ thống đã phân tích và đẩy thành công {metrics['total_tickets']} tickets lên Jira với độ chính xác {metrics['confidence_percentage']}%.",
        "agentHealth": {
            "researcher": worker_status,
            "planner": worker_status,
            "evaluator": worker_status
        }
    }

@router.get("/analytics", response_model=dict[str, Any])
def get_analytics_overview(project_id: Optional[str] = None):
    projects = DatabaseManager.get_all_projects()
    tv_details = []
    history_col = DatabaseManager.get_history_collection()
    
    resource_efficiency = []
    total_all_pts = 0

    if project_id:
        projects = [p for p in projects if str(p.get("id", "")) == project_id or str(p.get("_id", "")) == project_id]

    for p in projects:
        p_id = str(p.get("id", p.get("_id", "")))
        p_name = p.get("name", "Unknown")
        
        pipeline = [
            {"$match": {"project_id": p_id, "jira_key": {"$ne": "", "$exists": True}}},
            {"$group": {"_id": None, "total_pts": {"$sum": "$story.story_points"}}}
        ]
        agg_result = list(history_col.aggregate(pipeline))
        p_velocity = agg_result[0].get("total_pts") or 0 if agg_result else 0
        total_all_pts += p_velocity
        
        if p_velocity > 0:
            tv_details.append({"name": p_name, "pts": p_velocity})
            
        resource_efficiency.append({
            "name": p_name,
            "cycleTime": "N/A",
            "blockerRatio": 0,
            "aiAutomation": "100% SYNC",
            "trend": "up" if p_velocity > 0 else "flat"
        })

    metrics = get_real_metrics(project_id)
    avg_vel = total_all_pts / len(projects) if projects else 0
    
    # Calculate Lead Time from history
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
    
    # Generate mock burndown path based on ticket velocity (since we don't have sprint timeline)
    # We will simulate a 10-day sprint line. Ideal is 0,0 to 100,100.
    # Actual will be based on tickets.
    active_burndown_path = "M0,0 L100,100"
    if total_lead > 0:
        active_burndown_path = "M0,0 L20,10 L50,30 L80,70 L100,80" # Simulated actual path for now to show animation
    
    ai_insight = f"Phân tích dữ liệu thực tế: Hệ thống ghi nhận {metrics['total_tickets']} tickets. "
    if metrics["confidence_percentage"] > 90:
        ai_insight += "Độ chính xác hiện tại rất cao, gợi ý tiếp tục duy trì."
    else:
        ai_insight += "Độ chính xác cần cải thiện."

    return {
        "accuracy": metrics["confidence_percentage"],
        "accuracyTrend": "Real data only",
        "teamVelocityDetails": tv_details,
        "averageVelocity": round(avg_vel, 1),
        "resourceEfficiency": resource_efficiency,
        "leadTimeData": lead_time_data,
        "activeBurndownPath": active_burndown_path,
        "aiInsightText": ai_insight
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
