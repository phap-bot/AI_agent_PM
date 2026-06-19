import sys
from pathlib import Path
src_path = str(Path('d:/Antigravity/AI_Agent_PM_PRJ/src'))
sys.path.append(src_path)
from dotenv import load_dotenv
load_dotenv('d:/Antigravity/AI_Agent_PM_PRJ/src/ai_scrum_master/.env')
from ai_scrum_master.actions.jira import JiraTool
jira = JiraTool()
url = f"{jira.config.base_url.rstrip('/')}/rest/agile/1.0/board/{jira.config.board_id}/sprint"
resp = jira.http_client.get_json(url=url, basic_auth=(jira.config.email, jira.config.api_token), headers={'Accept': 'application/json'})
print('Status:', resp.status_code)
print('Response:', resp.json_body)
