import subprocess
import json
import os

OWNER = "microsoft"
NAME = "vscode"
LABEL = "agent-host"

QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    issues(states: [CLOSED], labels: ["agent-host"], first: 50, after: $cursor) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        body
        timelineItems(itemTypes: [CLOSED_EVENT], first: 10) {
          nodes {
            ... on ClosedEvent {
              closer {
                ... on PullRequest {
                  number
                  title
                  body
                  files(first: 100) {
                    nodes {
                      path
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

def fetch_issues():
    has_next_page = True
    cursor = None
    all_issues = []
    
    while has_next_page:
        cmd = [
            "gh", "api", "graphql",
            "-F", f"owner={OWNER}",
            "-F", f"name={NAME}",
            "-f", f"query={QUERY}"
        ]
        if cursor:
            cmd.extend(["-F", f"cursor={cursor}"])
            
        print(f"Fetching page with cursor: {cursor}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            print("Error executing gh api:")
            print(result.stderr)
            break
            
        data = json.loads(result.stdout)
        
        if "errors" in data:
            print("GraphQL Errors:")
            print(json.dumps(data["errors"], indent=2))
            break
            
        issues_data = data["data"]["repository"]["issues"]
        all_issues.extend(issues_data["nodes"])
        
        has_next_page = issues_data["pageInfo"]["hasNextPage"]
        cursor = issues_data["pageInfo"]["endCursor"]
        
    return all_issues

def process_issues(issues):
    dataset = []
    ground_truth = []
    
    for issue in issues:
        issue_number = issue.get("number")
        if not issue_number:
            continue
            
        # Find the PR that closed the issue
        closer_pr = None
        timeline = issue.get("timelineItems", {}).get("nodes", [])
        for event in timeline:
            if not event:
                continue
            closer = event.get("closer")
            if closer and "number" in closer:
                closer_pr = closer
                break
                
        if not closer_pr:
            # Skip issues that were closed without a PR
            continue
            
        # Prepare expected modules (files changed in the PR)
        expected_modules = []
        for file_node in closer_pr.get("files", {}).get("nodes", []):
            if file_node and "path" in file_node:
                expected_modules.append(file_node["path"])
                
        # Prepare expected behaviors (PR title and body)
        expected_behaviors = [f"{closer_pr.get('title', '')} (PR #{closer_pr.get('number')})"]
        
        # We can also add some of the PR body to expected behaviors if needed, 
        # but the title is usually the most concise summary of the behavior change.
        
        # Construct dataset entry
        dataset_entry = {
            "id": f"VS-{issue_number}",
            "input": {
                "title": issue.get("title", ""),
                "body": issue.get("body", "")
            },
            "metadata": {
                "labels": [LABEL],
                "url": f"https://github.com/{OWNER}/{NAME}/issues/{issue_number}",
                "state": "CLOSED"
            }
        }
        dataset.append(dataset_entry)
        
        # Construct ground truth entry
        ground_truth_entry = {
            "id": f"VS-{issue_number}",
            "labels": ["bug", LABEL], # Defaulting to bug, can be improved
            "expected_modules": expected_modules,
            "expected_behaviors": expected_behaviors,
            "expected_questions": [] # Questions are harder to extract automatically without an LLM
        }
        ground_truth.append(ground_truth_entry)
        
    return dataset, ground_truth

if __name__ == "__main__":
    print(f"Starting fetch for {OWNER}/{NAME} with label {LABEL}")
    raw_issues = fetch_issues()
    print(f"Fetched {len(raw_issues)} closed issues.")
    
    dataset, ground_truth = process_issues(raw_issues)
    print(f"Found {len(dataset)} issues closed by a Pull Request.")
    
    dataset_path = "d:/Antigravity/AI_Agent_PM_PRJ/data/vscode_closed_dataset.json"
    gt_path = "d:/Antigravity/AI_Agent_PM_PRJ/data/vscode_real_groundtruth.json"
    
    with open(dataset_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
        
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2, ensure_ascii=False)
        
    print(f"Dataset saved to {dataset_path}")
    print(f"Ground truth saved to {gt_path}")
