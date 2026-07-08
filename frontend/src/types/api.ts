export interface ApiResponseMeta {
  endpoint: string;
  project_id?: string | null;
  generated_at: string;
}

export interface ApiResponseEnvelope<T> {
  success: boolean;
  data: T;
  meta: ApiResponseMeta;
}

export interface GenerateStoriesRequest {
  requirement: string;
  n_results?: number;
  allow_fallback_without_context?: boolean;
  forced_context_docs?: string[];
  project_id?: string;
  user_id?: string;
}

export interface IngestRequest {
  raw_docs_dir?: string;
  project_id?: string;
}

export interface IngestResponse {
  collection: string;
  source_dir: string;
  files_indexed: number;
  chunks_indexed: number;
  skipped_count: number;
  indexed_files?: string[];
  skipped_files?: string[];
}

export interface IngestJobResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface IngestStatusResponse {
  job_id: string;
  status: string; // processing | completed | failed | not_found
  message: string;
  result: IngestResponse | null;
}

export interface ResearchContext {
  documents: string[];
  ids: string[];
  metadatas: any[];
  distances: (number | null)[];
  matches: any[];
  retrieved_sources: any[];
  selected_context_sources: any[];
  ignored_context_sources: any[];
  context_snippets: string[];
  planning_brief: Record<string, any>;
  retrieval_status: string;
  retrieval_threshold: number;
  raw_match_count: number;
  confidence: number;
  quality_gate: Record<string, any>;
  route: Record<string, any>;
  required_sources: string[];
  optional_sources: string[];
  missing_required_sources: string[];
  missing_optional_sources: string[];
  latency_ms: number;
  stage_latencies_ms: Record<string, number>;
  warnings: string[];
}

export interface StoryDraft {
  title: string;
  requirement: string;
  story_type: string;
  user_story: string;
  acceptance_criteria: string[];
  story_points: number | null;
  tasks: {
    be: string[];
    fe: string[];
    qa: string[];
  };
  definition_of_done: string[];
  priority: string;
  planning_status: string;
  clarification_questions: string[];
  assumptions: string[];
  story_splits: any[];
  sprint_allocation: any[];
  context_sources: any[];
  context_quality: Record<string, any>;
  planner_quality: Record<string, any>;
  route: Record<string, any>;
  latency_ms: number;
  stage_latencies_ms: Record<string, number>;
  repair_attempts_used: number;
  timed_out: boolean;
  failure_type: string;
  warnings: string[];
}

export interface EvaluationResult {
  status: string; // APPROVED | REVISION
  issues: string[];
  revision_instructions: string[];
  dod_score: Record<string, any>;
  warnings: string[];
}

export interface PreparedAction {
  ready: boolean;
  payload?: any;
  subtasks?: any[] | string | null;
  warnings: string[];
}

export interface ActionExecutionResult {
  ready: boolean;
  executed: boolean;
  payload?: any;
  created?: any;
  failed: any[];
  warnings: string[];
  status_code?: number | null;
}

export interface ActionPlan {
  jira: PreparedAction;
  slack: PreparedAction;
}

export interface ActionExecutionPlan {
  jira: ActionExecutionResult;
  slack: ActionExecutionResult;
}

export interface ActionPreviewRequest {
  story?: StoryDraft;
  evaluation?: EvaluationResult;
}

export interface GenerateStoriesResponse {
  context: ResearchContext;
  story: StoryDraft | null;
  evaluation: EvaluationResult;
  actions: ActionPlan;
  next_steps: string[];
}

export interface GenerateJobResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface GenerateStatusResponse {
  job_id: string;
  status: string; // processing | completed | failed
  stage?: string;
  message: string;
  result?: GenerateStoriesResponse | null;
  partial_result?: {
    context?: ResearchContext;
    story?: StoryDraft;
  } | null;
}

export interface JiraConfig {
  base_url: string;
  project_key: string;
  email: string;
  api_token: string;
  issue_type: string;
  subtask_issue_type: string;
  board_id: string;
}

export interface SlackConfig {
  webhook_url: string;
  mention_user_id: string;
  dev_channel_id: string;
  qa_channel_id: string;
}

export interface GithubConfig {
  repository: string;
  base_branch: string;
  api_token: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  jira_config?: Partial<JiraConfig>;
  slack_config?: Partial<SlackConfig>;
  github_config?: Partial<GithubConfig>;
  created_at?: string;
  updated_at?: string;
}

export interface CreateProjectInput {
  name: string;
  description?: string;
}

export interface UpdateProjectInput {
  name?: string;
  description?: string;
  jira_config?: Partial<JiraConfig>;
  slack_config?: Partial<SlackConfig>;
  github_config?: Partial<GithubConfig>;
}

export interface HistoryRecord {
  id: string;
  requirement: string;
  story?: StoryDraft;
  jira_key?: string;
  result?: GenerateStoriesResponse | Record<string, unknown>;
  project_id?: string | null;
  created_at?: string;
}

export interface SprintBoardIssue {
  key: string;
  summary?: string;
  status: string;
  type?: string;
  assignee?: Record<string, unknown> | string | null;
  parent_key?: string | null;
}

export interface SprintBoardData {
  sprint: Record<string, unknown>;
  issues: SprintBoardIssue[];
}

export interface SprintCreateResponse {
  message: string;
  sprint: Record<string, unknown>;
}

export interface SprintActionResponse {
  success: boolean;
  error?: string;
  status_code?: number | null;
  new_status?: string;
  [key: string]: unknown;
}

export interface DashboardTicket {
  key: string;
  title: string;
  agents: string[];
  priority: string;
  status: string;
  status_category?: string;
  story_points?: number;
}

export interface DashboardManagementResponse {
  sprintName: string;
  sprintEndDate: string;
  sprintProgress: number;
  totalTickets: number;
  totalTicketsTrend: string;
  aiConfidenceScore: number;
  teamVelocity: number;
  activeSprintTickets: DashboardTicket[];
  agentInsight: string;
  agentHealth: Record<string, string>;
  statusBreakdown: {
    todo: number;
    in_progress: number;
    done: number;
  };
  burndownData: Array<{ label: string; count: number }>;
  jiraConnected: boolean;
  totalSprintPoints: number;
  doneSprintPoints: number;
}

export interface AnalyticsVelocityDetail {
  name: string;
  pts: number;
  done_pts: number;
  total_pts: number;
}

export interface AnalyticsResourceEfficiencyItem {
  name: string;
  cycleTime: string;
  blockerRatio: number;
  aiAutomation: string;
  trend: string;
  done: number;
  in_progress: number;
  todo: number;
}

export interface AnalyticsOverviewResponse {
  accuracy: number;
  accuracyTrend: string;
  teamVelocityDetails: AnalyticsVelocityDetail[];
  averageVelocity: number;
  resourceEfficiency: AnalyticsResourceEfficiencyItem[];
  leadTimeData: Record<string, { count: number; percentage: number }>;
  activeBurndownPath: string;
  aiInsightText: string;
  jiraConnected: boolean;
  statusBreakdown: {
    todo: number;
    in_progress: number;
    done: number;
  };
  totalSprintPoints: number;
  doneSprintPoints: number;
  totalSprintIssues: number;
}

export interface TeamMemberNode {
  name: string;
  task: string;
  status: string;
}

export interface TeamMembersResponse {
  agentEfficiency: number;
  agentVelocityAudit: string;
  activeAgentNodes: TeamMemberNode[];
  members: unknown[];
  teamSeats: {
    used: number;
    total: number;
  };
  aiAgentTokens: number;
  pendingInvites: number;
}
