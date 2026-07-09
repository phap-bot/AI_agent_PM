import type {
  ApiResponseEnvelope,
  GenerateStoriesRequest,
  ActionPreviewRequest,
  ActionPlan,
  ActionExecutionPlan,
  IngestRequest,
  IngestResponse,
  IngestJobResponse,
  IngestStatusResponse,
  GenerateJobResponse,
  GenerateStatusResponse,
  HistoryRecord,
  SprintBoardData,
  SprintCreateResponse,
  SprintActionResponse,
  Project,
  CreateProjectInput,
  UpdateProjectInput,
  DashboardManagementResponse,
  AnalyticsOverviewResponse,
  TeamMembersResponse
} from '../types/api';

const API_BASE_URL = '/api';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `Failed with status ${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json() as Record<string, unknown>;
      if (errorData?.detail) {
        errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      } else if (errorData?.error && typeof errorData.error === 'object') {
        const error = errorData.error as { message?: string; details?: unknown };
        errorMessage = error.message || errorMessage;
        if (error.details) {
          errorMessage += ` - ${JSON.stringify(error.details)}`;
        }
      } else {
        errorMessage += ` ${JSON.stringify(errorData)}`;
      }
    } catch (e) {
      // Ignored if response is not JSON
    }
    throw new Error(errorMessage);
  }

  const payload = await response.json() as T | ApiResponseEnvelope<T>;
  if (payload && typeof payload === 'object' && 'success' in payload && 'data' in payload) {
    const envelope = payload as ApiResponseEnvelope<T> & { error?: { message?: string } };
    if (envelope.success === false) {
      const message = envelope?.error?.message || envelope?.meta?.endpoint || 'Request failed';
      throw new Error(message);
    }
    return envelope.data;
  }

  return payload as T;
}

export async function generateStoriesAsync(request: GenerateStoriesRequest): Promise<GenerateJobResponse> {
  const response = await fetch(`${API_BASE_URL}/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return handleResponse<GenerateJobResponse>(response);
}

export async function getGenerateStatus(jobId: string): Promise<GenerateStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/generate/status/${jobId}`);

  return handleResponse<GenerateStatusResponse>(response);
}

export async function cancelGenerateJob(jobId: string): Promise<{ job_id: string; status: string; cancelled: boolean }> {
  const response = await fetch(`${API_BASE_URL}/generate/cancel/${jobId}`, {
    method: 'POST',
  });

  return handleResponse<{ job_id: string; status: string; cancelled: boolean }>(response);
}

export function sendGenerateCancelBeacon(jobId: string): boolean {
  const url = `${API_BASE_URL}/generate/cancel/${jobId}`;
  if (navigator.sendBeacon) {
    return navigator.sendBeacon(url, new Blob([], { type: 'application/json' }));
  }

  fetch(url, { method: 'POST', keepalive: true }).catch(() => undefined);
  return true;
}

export async function previewJiraAction(request: ActionPreviewRequest): Promise<ActionPlan> {
  const response = await fetch(`${API_BASE_URL}/actions/jira/preview`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return handleResponse<ActionPlan>(response);
}

export async function previewSlackAction(request: ActionPreviewRequest): Promise<ActionPlan> {
  const response = await fetch(`${API_BASE_URL}/actions/slack/preview`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return handleResponse<ActionPlan>(response);
}

export async function executeJiraAction(request: ActionPreviewRequest): Promise<ActionExecutionPlan> {
  const response = await fetch(`${API_BASE_URL}/actions/jira/execute`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return handleResponse<ActionExecutionPlan>(response);
}

export async function executeAllActions(request: ActionPreviewRequest): Promise<ActionExecutionPlan> {
  const response = await fetch(`${API_BASE_URL}/actions/execute-all`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return handleResponse<ActionExecutionPlan>(response);
}

export async function ingestDocuments(request: IngestRequest = {}): Promise<IngestResponse> {
  const response = await fetch(`${API_BASE_URL}/ingest`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  return handleResponse<IngestResponse>(response);
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

  return handleResponse<IngestJobResponse>(response);
}

export async function getIngestStatus(jobId: string): Promise<IngestStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/ingest/status/${jobId}`);

  return handleResponse<IngestStatusResponse>(response);
}

export async function fetchHistory(projectId?: string): Promise<HistoryRecord[]> {
  let url = `${API_BASE_URL}/history`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url);
  return handleResponse<HistoryRecord[]>(response);
}

export async function deleteHistory(historyId: string): Promise<{ deleted: boolean; history_id: string }> {
  const response = await fetch(`${API_BASE_URL}/history/${historyId}`, {
    method: 'DELETE'
  });
  return handleResponse<{ deleted: boolean; history_id: string }>(response);
}

export async function fetchSprintBoard(projectId?: string): Promise<SprintBoardData> {
  let url = `${API_BASE_URL}/sprint`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url);
  return handleResponse<SprintBoardData>(response);
}

export async function createSprint(projectId?: string): Promise<SprintCreateResponse> {
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
  return handleResponse<SprintCreateResponse>(response);
}

export async function completeSprint(
  sprintId: string,
  payload: { move_open_to: string; open_issues: string[] },
  projectId?: string,
): Promise<SprintActionResponse> {
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
  return handleResponse<SprintActionResponse>(response);
}

export async function deleteSprintIssue(issueKey: string, projectId?: string): Promise<SprintActionResponse> {
  let url = `${API_BASE_URL}/sprint/issue/${issueKey}`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url, { method: 'DELETE' });
  return handleResponse<SprintActionResponse>(response);
}

export async function updateSprintIssueStatus(issueKey: string, status: string, projectId?: string): Promise<SprintActionResponse> {
  let url = `${API_BASE_URL}/sprint/issue/${issueKey}/status`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  return handleResponse<SprintActionResponse>(response);
}

export async function getProjects(): Promise<Project[]> {
  const response = await fetch(`${API_BASE_URL}/projects`);
  return handleResponse<Project[]>(response);
}

export async function fetchJiraPriorities(projectId: string): Promise<Array<Record<string, unknown>>> {
  if (!projectId) return [];
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/jira-priorities`);
  return handleResponse<Array<Record<string, unknown>>>(response);
}

export async function getProject(projectId: string): Promise<Project> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`);
  return handleResponse<Project>(response);
}

export async function createProject(data: CreateProjectInput): Promise<Project> {
  const response = await fetch(`${API_BASE_URL}/projects`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  return handleResponse<Project>(response);
}

export async function updateProject(projectId: string, data: UpdateProjectInput): Promise<Project> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  return handleResponse<Project>(response);
}

export async function deleteProject(projectId: string): Promise<{ deleted: boolean; project_id: string }> {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: 'DELETE',
  });
  return handleResponse<{ deleted: boolean; project_id: string }>(response);
}

export async function fetchManagementDashboard(projectId?: string): Promise<DashboardManagementResponse> {
  let url = `${API_BASE_URL}/dashboard/management`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url);
  return handleResponse<DashboardManagementResponse>(response);
}

export async function fetchAnalyticsOverview(projectId?: string): Promise<AnalyticsOverviewResponse> {
  let url = `${API_BASE_URL}/dashboard/analytics`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url);
  return handleResponse<AnalyticsOverviewResponse>(response);
}

export async function fetchTeamMembers(projectId?: string): Promise<TeamMembersResponse> {
  let url = `${API_BASE_URL}/dashboard/team`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url);
  return handleResponse<TeamMembersResponse>(response);
}
