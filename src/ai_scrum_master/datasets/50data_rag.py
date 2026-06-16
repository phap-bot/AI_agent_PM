import json
from pathlib import Path

import requests

OUT_DIR = Path("benchmarks/planner")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "apache_jira_issues_50.jsonl"

JIRA_BASE_URL = "https://issues.apache.org/jira"

params = {
    "jql": "project = SPARK AND issuetype in (Epic, Story, Task, Bug) ORDER BY created DESC",
    "maxResults": 500,
    "fields": "summary,description,issuetype,priority,status,labels,components,created,updated,issuelinks,parent,subtasks,customfield_12310243,customfield_12311120"
}

url = f"{JIRA_BASE_URL}/rest/api/2/search"

response = requests.get(url, params=params, timeout=60)
response.raise_for_status()

data = response.json()
issues = data.get("issues", [])

with open(OUT_FILE, "w", encoding="utf-8") as f:
    for issue in issues:
        fields = issue.get("fields", {})

        row = {
            "id": issue.get("key"),
            "source": "apache_public_jira_api",
            "summary": fields.get("summary"),
            "description": fields.get("description"),
            "issue_type": fields.get("issuetype", {}).get("name") if fields.get("issuetype") else None,
            "priority": fields.get("priority", {}).get("name") if fields.get("priority") else None,
            "status": fields.get("status", {}).get("name") if fields.get("status") else None,
            "labels": fields.get("labels", []),
            "components": [
                c.get("name") for c in fields.get("components", [])
            ],
            "created": fields.get("created"),
            "updated": fields.get("updated"),
            "story_points": fields.get("customfield_12310243") or fields.get("customfield_12311120"),
            "parent": fields.get("parent", {}).get("key") if fields.get("parent") else None,
            "subtasks": [s.get("key") for s in fields.get("subtasks", [])],
            "issuelinks": [
                {
                    "type": l.get("type", {}).get("name"),
                    "outwardIssue": l.get("outwardIssue", {}).get("key"),
                    "inwardIssue": l.get("inwardIssue", {}).get("key")
                } for l in fields.get("issuelinks", [])
            ]
        }

        json.dump(row, f, ensure_ascii=False)
        f.write("\n")

print(f"Saved {len(issues)} issues to {OUT_FILE}")