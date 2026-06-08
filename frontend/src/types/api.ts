export interface GenerateStoriesRequest {
  requirement: string;
  n_results?: number;
  allow_fallback_without_context?: boolean;
}

export interface IngestRequest {
  raw_docs_dir?: string;
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
  priority?: string;
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
  message: string;
  result?: GenerateStoriesResponse | null;
  partial_result?: {
    context?: ResearchContext;
    story?: StoryDraft;
  } | null;
}
