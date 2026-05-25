---
name: repo-scaffold
description: Generate the exact repo skeleton and shell commands needed to scaffold the AI Scrum Master Agent codebase.
tags: [#scaffold, #structure, #filesystem, #bootstrap]
slash: /repo-scaffold
---

# Purpose
Create or validate the project folder structure before implementation begins.

# When to use
- When bootstrapping the repository
- When aligning implementation with a prescribed project layout
- Before writing FastAPI, CrewAI, Streamlit, or ChromaDB modules

# Inputs
- Desired folder tree
- Required starter files
- Platform constraints for shell commands

# Outputs
- Shell script or command list
- Directory checklist
- File creation sequence

# Rules
- Match the required structure exactly.
- Group files by runtime responsibility: api, agents, core, ui, tests, evaluation, data.
- Prefer idempotent scaffold commands when possible.

# Example
/repo-scaffold
Input: Create the ai_scrum_master layout from prompt.md.
