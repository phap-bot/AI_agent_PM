---
name: pipeline-architect
description: Extract the end-to-end AI delivery pipeline from product documents and convert it into agentic system structure.
tags: [#pipeline, #architecture, #agents, #design]
slash: /pipeline-architect
---

# Purpose
Map a business workflow into an AI-agent pipeline with clear stages, responsibilities, tools, and failure paths.

# When to use
- When reading a project brief or product requirement
- When translating a document into system architecture
- When extracting agent boundaries from a manual workflow

# Inputs
- Raw project brief
- Process description
- Existing pipeline notes

# Outputs
- Stage-by-stage pipeline
- Actor and tool map
- Agent responsibilities
- Key decision points and failure modes

# Rules
- Preserve the original business intent.
- Distinguish between reasoning steps and action steps.
- Explicitly identify optional human approval points.
- Highlight ambiguity, oversized scope, and integration failure paths.

# Example
/pipeline-architect
Input: Convert the AI Scrum Master Agent concept note into a production pipeline.
