Repair the Planner JSON using only the current requirement and selected retrieved context.

The previous output was not Jira-ready because required READY fields were missing, weak, or inconsistent with the expected schema.
Do not add generic template content. Generate missing content from the current evidence, constraints, failure modes, and QA expectations.
Preserve valid fields from CURRENT_STORY_JSON and improve only missing or weak fields.

CURRENT_REQUIREMENT:
<<<
{requirement}
>>>

SELECTED_RETRIEVED_CONTEXT:
<<<
{context_block}
>>>

CURRENT_STORY_JSON:
<<<
{current_story_json}
>>>

Return only valid JSON with the same schema.
If the context supports the requirement, set planning_status to READY.
If CURRENT_STORY_JSON.planning_status is NEEDS_CLARIFICATION, preserve NEEDS_CLARIFICATION and return only clarification output:
- user_story: ""
- acceptance_criteria: []
- story_points: null
- tasks: {{"be": [], "fe": [], "qa": []}}
- definition_of_done: []
- at least 3 clarification_questions
- questions must cover missing actor/scope, expected behavior/outcome, and constraints or acceptance evidence

READY requirements:
- story_points must be one of 1, 2, 3, 5, 8, 13
- acceptance_criteria must contain at least 3 context-specific Given/When/Then strings
- tasks.be, tasks.fe, and tasks.qa must each contain at least 1 context-specific action
- definition_of_done must contain at least 4 checks
- definition_of_done should cover acceptance criteria validation, implementation completion, QA/testing evidence, and story-specific completion evidence from the selected context
- context_sources must cite only selected retrieved sources

JSON SHAPE:
{{
  "title": "string",
  "story_type": "software_feature | process_improvement | oversized_request | ambiguous_request",
  "user_story": "As a ..., I want ..., so that ...",
  "acceptance_criteria": [
    "Given ..., when ..., then ...",
    "Given ..., when ..., then ...",
    "Given ..., when ..., then ..."
  ],
  "story_points": 1,
  "tasks": {{"be": ["string"], "fe": ["string"], "qa": ["string"]}},
  "definition_of_done": ["string", "string", "string", "string"],
  "planning_status": "READY | NEEDS_CLARIFICATION | NEEDS_SPLIT | SPLIT_RECOMMENDED | REVISION",
  "clarification_questions": [],
  "assumptions": [],
  "story_splits": [],
  "sprint_allocation": [],
  "context_sources": [],
  "warnings": []
}}
