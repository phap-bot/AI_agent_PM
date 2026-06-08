import type {
  GenerateStoriesRequest,
  GenerateStoriesResponse,
  ActionPreviewRequest,
  ActionPlan,
  ActionExecutionPlan,
  IngestRequest,
  IngestResponse,
  IngestJobResponse,
  IngestStatusResponse
} from '../types/api';

const API_BASE_URL = '/api';

async function handleResponse(response: Response) {
  if (!response.ok) {
    let errorMessage = `Failed with status ${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData?.error?.message) {
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

export async function fetchSprintBoard(projectId?: string) {
  let url = `${API_BASE_URL}/sprint`;
  if (projectId) {
    url += `?project_id=${projectId}`;
  }
  const response = await fetch(url);
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
