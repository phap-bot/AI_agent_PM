# AI Scrum Master Agent Requirements

## Goal
Build an AI Scrum Master Agent that converts raw stakeholder requests into validated, sprint-ready Jira work items with optional PM approval and Slack notification.

## Primary Users
- PM or Scrum Master who receives raw stakeholder requests.
- Development team members who consume Jira stories and subtasks.
- QA who validates acceptance criteria and test scope.

## MVP Scope
1. Accept a raw requirement from API or demo UI.
2. Retrieve relevant project context from local ChromaDB.
3. Generate one or more user stories.
4. Validate story quality before action.
5. Return a structured response suitable for human review.

## Functional Requirements

### Intake
- The system shall accept a raw requirement as text.
- The system shall support clear, ambiguous, and oversized requests.

### Researcher
- The system shall query persistent ChromaDB for project context.
- The system shall use `nomic-embed-text` through local Ollama for embeddings.
- The system shall return retrieved documents, ids, source metadata, distances, warnings, and confidence.
- If retrieval returns no useful context, the system shall continue with reduced confidence and explicit warnings.

### Planner
- The system shall produce user stories in As a / I want / So that format.
- Each story shall include at least 3 acceptance criteria in Given / When / Then format.
- Story points shall use Fibonacci values: 1, 2, 3, 5, 8, 13.
- Tasks shall be separated into BE, FE, and QA.
- Each story shall include a definition of done.

### Evaluator
- The system shall return either APPROVED or REVISION.
- The evaluator shall check story format, AC count, Fibonacci story points, and task breakdown.
- Revision loops shall stop after 3 rounds and escalate to PM.

### Approval and Action
- The system shall not create Jira issues before evaluation passes.
- Human approval shall be supported before Jira/Slack actions.
- Jira 401 errors shall trigger auth refresh and retry up to 3 times before escalation.

## Non-Functional Requirements
- The system shall run locally with Ollama on port 11434.
- Runtime defaults shall be conservative for NVIDIA RTX 3050 4GB VRAM.
- ChromaDB data shall persist locally under `data/chromadb/`.
- Tests shall be implemented with pytest.

## Out of Scope for Initial MVP
- Full Jira issue creation without human approval.
- Advanced permission management.
- Multi-project tenant support.
- Production Slack app installation flow.
