import json
from ai_scrum_master.agents.planner import PlannerAgent
from ai_scrum_master.core.story_validator import is_task_actionable_for_group, filter_domain_contaminated_items

task1 = "Implement booking creation handler using POST /api/v1/bookings with validation for required fields: phone (string), address_line (string), preferred_date (date dd/mm/yyyy), preferred_slot (time frame)"
task2 = "Build booking status tracking service to maintain state across GET /api/v1/bookings/{bookingId} responses"
task3 = "Create admin endpoint handler PATCH /api/v1/admin/jobs/{bookingId}/assign for technician assignment"

tasks = [task1, task2, task3]
req = "Customer Booking System - Core Appointment Scheduling"

agent = PlannerAgent()
cleaned = agent._clean_tasks(req, {"be": tasks}, [])
print("Cleaned tasks:")
print(cleaned)

print("\nValidation individual:")
for i, t in enumerate(tasks):
    print(f"Task {i+1} actionable:", is_task_actionable_for_group(t, "be"))
    
print("\nDomain contamination:")
kept, removed = filter_domain_contaminated_items(req, tasks)
print("Kept:", kept)
print("Removed:", removed)
