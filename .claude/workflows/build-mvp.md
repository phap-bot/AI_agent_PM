# /wf-build-mvp
Tags: #workflow #mvp #implementation-plan

## Goal
Ship the smallest end-to-end version of the pipeline before adding advanced reliability layers.

## Suggested phases
1. Repo and dependency setup -> /repo-scaffold, /poetry-setup, /ollama-runtime
2. Retrieval foundation -> /rag-design and /vector-store-setup
3. Clear request planning -> /story-write
4. Quality gate -> /story-eval
5. Human review -> /approval-flow
6. External action -> /jira-action and /slack-notify
7. Reliability pass -> /trace-observe and /failure-playbook

## Deliverables
- Happy path implementation order
- MVP acceptance checklist
- Deferred work list
