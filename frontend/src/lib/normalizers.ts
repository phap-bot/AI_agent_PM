import type { StoryDraft } from '../types/api';

export function normalizeStoryDraft(draft: StoryDraft | null | undefined, originalRequirement?: string): StoryDraft {
  const defaultTasks = { be: [], fe: [], qa: [] };
  
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
    tasks: draft.tasks || defaultTasks,
    acceptance_criteria: draft.acceptance_criteria || [],
    definition_of_done: draft.definition_of_done || [],
    priority: draft.priority || 'Medium',
  };
}
