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

export async function generateStoriesAsync(request: GenerateStoriesRequest): Promise<GenerateJobResponse> {
  const response = await fetch(`${API_BASE_URL}/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(`Failed to generate stories: ${response.status} ${response.statusText} ${JSON.stringify(errorData)}`);
  }

  return response.json();
}

export async function getGenerateStatus(jobId: string): Promise<GenerateStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/generate/status/${jobId}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(`Failed to get generate status: ${response.status} ${response.statusText} ${JSON.stringify(errorData)}`);
  }

  return response.json();
}

export async function previewJiraAction(request: ActionPreviewRequest): Promise<ActionPlan> {
  const response = await fetch(`${API_BASE_URL}/actions/jira/preview`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(`Failed to preview Jira action: ${response.status} ${response.statusText} ${JSON.stringify(errorData)}`);
  }

  return response.json();
}

export async function previewSlackAction(request: ActionPreviewRequest): Promise<ActionPlan> {
  const response = await fetch(`${API_BASE_URL}/actions/slack/preview`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(`Failed to preview Slack action: ${response.status} ${response.statusText} ${JSON.stringify(errorData)}`);
  }

  return response.json();
}

export async function executeJiraAction(request: ActionPreviewRequest): Promise<ActionExecutionPlan> {
  const response = await fetch(`${API_BASE_URL}/actions/jira/execute`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(`Failed to execute Jira action: ${response.status} ${response.statusText} ${JSON.stringify(errorData)}`);
  }

  return response.json();
}

export async function ingestDocuments(request: IngestRequest = {}): Promise<IngestResponse> {
  const response = await fetch(`${API_BASE_URL}/ingest`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(`Failed to ingest documents: ${response.status} ${response.statusText} ${JSON.stringify(errorData)}`);
  }

  return response.json();
}

export async function uploadDocumentsAsync(files: FileList): Promise<IngestJobResponse> {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  const response = await fetch(`${API_BASE_URL}/ingest/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(`Failed to upload documents: ${response.status} ${response.statusText} ${JSON.stringify(errorData)}`);
  }

  return response.json();
}

export async function getIngestStatus(jobId: string): Promise<IngestStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/ingest/status/${jobId}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(`Failed to get ingest status: ${response.status} ${response.statusText} ${JSON.stringify(errorData)}`);
  }

  return response.json();
}
