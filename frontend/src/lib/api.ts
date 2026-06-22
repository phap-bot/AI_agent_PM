import type {
  GenerateStoriesRequest,
  GenerateStoriesResponse,
  ActionPreviewRequest,
  ActionPlan,
  ActionExecutionPlan,
  IngestRequest,
  IngestResponse,
  IngestJobResponse,
  IngestStatusResponse,
  GenerateJobResponse,
  GenerateStatusResponse
} from '../types/api';

const API_BASE_URL = '/api';

async function handleResponse(response: Response) {
  if (!response.ok) {
    let errorMessage = `Failed with status ${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData?.detail) {
        errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      } else if (errorData?.error?.message) {
        errorMessage = errorData.error.message;
        if (errorData.error.details) {
          errorMessage += ` - ${JSON.stringify(errorData.error.details)}`;
        }
      } else {
        errorMessage += ` ${JSON.stringify(errorData)}`;
      }
    } catch (e) {
      // Ignored if response is not JSON
    }
    throw new Error(errorMessage);
  }
  return response.json();
}

export async function generateStoriesAsync(request: GenerateStoriesRequest): Promise<GenerateJobResponse> {
  const response = await fetch(`${API_BASE_URL}/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return handleResponse(response);
}

export async function getGenerateStatus(jobId: string): Promise<GenerateStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/generate/status/${jobId}`);

  return handleResponse(response);
}

export async function previewJiraAction(request: ActionPreviewRequest): Promise<ActionPlan> {
  const response = await fetch(`${API_BASE_URL}/actions/jira/preview`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return handleResponse(response);
}

export async function previewSlackAction(request: ActionPreviewRequest): Promise<ActionPlan> {
  const response = await fetch(`${API_BASE_URL}/actions/slack/preview`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return handleResponse(response);
}

export async function executeJiraAction(request: ActionPreviewRequest): Promise<ActionExecutionPlan> {
  const response = await fetch(`${API_BASE_URL}/actions/jira/execute`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return handleResponse(response);
}

export async function executeAllActions(request: ActionPreviewRequest): Promise<ActionExecutionPlan> {
  const response = await fetch(`${API_BASE_URL}/actions/execute-all`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return handleResponse(response);
}

export async function ingestDocuments(request: IngestRequest = {}): Promise<IngestResponse> {
  const response = await fetch(`${API_BASE_URL}/ingest`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return handleResponse(response);
}

export async function uploadDocumentsAsync(files: FileList, projectId?: string): Promise<IngestJobResponse> {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  let url = `${API_BASE_URL}/ingest/upload`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }

  const response = await fetch(url, {
    method: 'POST',
    body: formData,
  });

  return handleResponse(response);
}

export async function getIngestStatus(jobId: string): Promise<IngestStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/ingest/status/${jobId}`);

  return handleResponse(response);
}

export async function fetchHistory(projectId?: string) {
  let url = `${API_BASE_URL}/history`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url);
  return handleResponse(response);
}

export async function deleteHistory(historyId: string) {
  const response = await fetch(`${API_BASE_URL}/history/${historyId}`, {
    method: 'DELETE'
  });
  return handleResponse(response);
}

export async function fetchSprintBoard(projectId?: string) {
  let url = `${API_BASE_URL}/sprint`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url);
  return handleResponse(response);
}

export async function createSprint(projectId?: string) {
  let url = `${API_BASE_URL}/sprint`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    }
  });
  return handleResponse(response);
}

export async function completeSprint(sprintId: string, payload: any, projectId?: string) {
  let url = `${API_BASE_URL}/sprint/${sprintId}/complete`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

export async function deleteSprintIssue(issueKey: string, projectId?: string) {
  let url = `${API_BASE_URL}/sprint/issue/${issueKey}`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url, { method: 'DELETE' });
  return handleResponse(response);
}

export async function updateSprintIssueStatus(issueKey: string, status: string, projectId?: string) {
  let url = `${API_BASE_URL}/sprint/issue/${issueKey}/status`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  return handleResponse(response);
}

export async function getProjects(): Promise<any[]> {
  const response = await fetch(`${API_BASE_URL}/projects`);
  return handleResponse(response);
}

export async function fetchJiraPriorities(projectId: string): Promise<any[]> {
  if (!projectId) return [];
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/jira-priorities`);
  return handleResponse(response);
}

export async function getProject(projectId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`);
  return handleResponse(response);
}

export async function createProject(data: any): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/projects`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  return handleResponse(response);
}

export async function updateProject(projectId: string, data: any): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  return handleResponse(response);
}

export async function deleteProject(projectId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: 'DELETE',
  });
  // 204 No Content won't have JSON body to parse, so just return true if ok
  if (response.status === 204) return true;
  return handleResponse(response);
}

// Real endpoints for dashboard features
export async function fetchManagementDashboard(projectId?: string): Promise<any> {
  let url = `${API_BASE_URL}/dashboard/management`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url);
  return handleResponse(response);
}

export async function fetchAnalyticsOverview(projectId?: string): Promise<any> {
  let url = `${API_BASE_URL}/dashboard/analytics`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url);
  return handleResponse(response);
}

export async function fetchTeamMembers(projectId?: string): Promise<any> {
  let url = `${API_BASE_URL}/dashboard/team`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url);
  return handleResponse(response);
}
