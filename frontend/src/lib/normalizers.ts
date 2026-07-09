import type { StoryDraft } from '../types/api';

export function normalizeStoryDraft(draft: StoryDraft | null | undefined, originalRequirement?: string): StoryDraft {
  const defaultTasks = { be: [], fe: [], qa: [] };
  const normalizeArray = (value: unknown): any[] => Array.isArray(value) ? value : [];
  
  if (!draft) {
    return {
      title: originalRequirement || '',
      requirement: originalRequirement || '',
      story_type: 'feature',
      user_story: '',
      acceptance_criteria: [],
      story_points: null,
      tasks: defaultTasks,
      definition_of_done: [],
      priority: 'Medium',
      planning_status: 'DRAFT',
      clarification_questions: [],
      assumptions: [],
      story_splits: [],
      sprint_allocation: [],
      context_sources: [],
      context_quality: {},
      planner_quality: {},
      route: {},
      latency_ms: 0,
      stage_latencies_ms: {},
      repair_attempts_used: 0,
      timed_out: false,
      failure_type: '',
      warnings: [],
    };
  }
  
  return {
    ...draft,
    title: draft.title || originalRequirement || draft.requirement || '',
    requirement: draft.requirement || originalRequirement || '',
    user_story: draft.user_story || '',
    tasks: {
      be: normalizeArray(draft.tasks?.be),
      fe: normalizeArray(draft.tasks?.fe),
      qa: normalizeArray(draft.tasks?.qa),
    },
    acceptance_criteria: normalizeArray(draft.acceptance_criteria),
    definition_of_done: normalizeArray(draft.definition_of_done),
    priority: draft.priority || 'Medium',
    planning_status: draft.planning_status || 'DRAFT',
    clarification_questions: normalizeArray(draft.clarification_questions),
    assumptions: normalizeArray(draft.assumptions),
    story_splits: normalizeArray(draft.story_splits),
    sprint_allocation: normalizeArray(draft.sprint_allocation),
    context_sources: normalizeArray(draft.context_sources),
    warnings: normalizeArray(draft.warnings),
  };
}
