import urllib.request
import json
try:
    req = urllib.request.Request('http://localhost:8000/dashboard/management?project_id=6a39edfbcd632e75be491bff')
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print("Status Breakdown:", data.get("statusBreakdown"))
        for t in data.get("activeSprintTickets", []):
            print(t["key"], t["status"], t["status_category"])
except Exception as e:
    print(e)
