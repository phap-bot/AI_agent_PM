from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from ai_scrum_master.core.utils.http_client import HttpClient, UrllibHttpClient
from ai_scrum_master.core.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class GithubConfig:
    repository: str
    api_token: str
    base_branch: str = "main"

    @property
    def is_configured(self) -> bool:
        return bool(self.repository and self.api_token)


class GithubTool:
    def __init__(self, config: GithubConfig | None = None, http_client: HttpClient | None = None) -> None:
        self.config = config or GithubConfig(repository="", api_token="")
        self.http_client = http_client or UrllibHttpClient()

    @classmethod
    def from_project(cls, project_id: str | None, http_client: HttpClient | None = None) -> GithubTool:
        if not project_id:
            return cls(http_client=http_client)
            
        from ai_scrum_master.core.utils.database import DatabaseManager
        project = DatabaseManager.get_project(project_id)
        if not project or not project.get("github_config"):
            return cls(http_client=http_client)
            
        db_config = project["github_config"]
        config = GithubConfig(
            repository=db_config.get("repository", ""),
            api_token=db_config.get("api_token", ""),
            base_branch=db_config.get("base_branch") or "main",
        )
        return cls(config=config, http_client=http_client)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"token {self.config.api_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Scrum-Master",
        }

    def _execute_with_retry(self, method: str, url: str, **kwargs: Any) -> Any:
        max_retries = 3
        backoff_factor = 1.5
        last_exception = None
        last_response = None

        for attempt in range(max_retries):
            try:
                if method.upper() == "GET":
                    response = self.http_client.get_json(
                        url=url,
                        headers=self._headers(),
                        timeout=15
                    )
                elif method.upper() == "POST":
                    response = self.http_client.post_json(
                        url=url,
                        payload=kwargs.get("json", {}),
                        headers=self._headers(),
                        timeout=15
                    )
                else:
                    raise ValueError(f"Unsupported method {method}")
                    
                last_response = response
                
                if 200 <= response.status_code < 300:
                    return response.json_body
                
                # If branch already exists, it's not a fatal error for our use-case, but we can return it.
                if response.status_code == 422 and "Reference already exists" in str(response.text):
                    return {"status": "exists", "message": "Branch already exists"}

                logger.warning(
                    "GitHub API error url=%s status=%s body=%s", 
                    url, response.status_code, response.text
                )
                if response.status_code in {401, 403, 404, 409, 422}:
                    # Unrecoverable errors (auth, not found, conflict, validation)
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
                    
            except Exception as e:
                last_exception = e
                logger.warning("GitHub API exception attempt=%s url=%s err=%s", attempt + 1, url, e)

            time.sleep(backoff_factor ** attempt)

        err_msg = f"Failed after {max_retries} retries."
        if last_exception:
            err_msg += f" Last error: {last_exception}"
        elif last_response:
            err_msg += f" Last status: {last_response.status_code}, Body: {last_response.text}"
            
        logger.error("GitHub API failed url=%s error=%s", url, err_msg)
        return {"error": err_msg}

    def create_feature_branch(self, branch_name: str) -> dict[str, Any]:
        """Creates a new branch on GitHub from the configured base_branch."""
        if not self.config.is_configured:
            return {"ready": False, "warnings": ["GitHub repository or token not configured."]}

        repo = self.config.repository.strip()
        if repo.startswith("https://github.com/"):
            repo = repo[19:]
        if repo.endswith(".git"):
            repo = repo[:-4]
            
        base_branch = self.config.base_branch.strip()
        
        logger.info("GitHub getting ref for base_branch=%s repo=%s", base_branch, repo)
        get_ref_url = f"https://api.github.com/repos/{repo}/git/refs/heads/{base_branch}"
        ref_data = self._execute_with_retry("GET", get_ref_url)
        
        if isinstance(ref_data, dict) and "error" in ref_data:
            err_text = ref_data['error']
            if "Git Repository is empty" in err_text:
                return {"ready": False, "warnings": [f"Kho lưu trữ '{repo}' đang trống. Vui lòng commit ít nhất 1 file (VD: README.md) lên branch '{base_branch}' để AI có thể tạo branch con."]}
            return {"ready": False, "warnings": [f"Failed to get base branch '{base_branch}': {err_text}"]}
            
        sha = ref_data.get("object", {}).get("sha")
        if not sha:
            return {"ready": False, "warnings": [f"Could not find SHA for base branch '{base_branch}'."]}

        logger.info("GitHub creating branch=%s from sha=%s", branch_name, sha)
        create_ref_url = f"https://api.github.com/repos/{repo}/git/refs"
        payload = {
            "ref": f"refs/heads/{branch_name}",
            "sha": sha
        }
        
        create_data = self._execute_with_retry("POST", create_ref_url, json=payload)
        
        if isinstance(create_data, dict) and "error" in create_data:
            return {"ready": False, "warnings": [f"Failed to create branch '{branch_name}': {create_data['error']}"]}
            
        if isinstance(create_data, dict) and create_data.get("status") == "exists":
            logger.info("GitHub branch %s already exists, proceeding safely", branch_name)
            return {"ready": True, "branch_url": f"https://github.com/{repo}/tree/{branch_name}"}

        branch_url = f"https://github.com/{repo}/tree/{branch_name}"
        logger.info("GitHub branch created successfully url=%s", branch_url)
        return {"ready": True, "branch_url": branch_url}
