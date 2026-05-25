---
name: ollama-runtime
description: Design safe local Ollama model setup for CrewAI on constrained GPU hardware.
tags: [#ollama, #llm-setup, #vram, #local-inference]
slash: /ollama-runtime
---

# Purpose
Specify how `core/llm_setup.py` should connect to local Ollama and avoid common VRAM or timeout failures.

# When to use
- When writing or reviewing `core/llm_setup.py`
- When selecting runtime defaults for local inference
- When troubleshooting model startup or memory issues

# Inputs
- Model name
- Ollama host and port
- Hardware limits
- Agent framework integration requirements

# Outputs
- Runtime setup guidance
- Safe default configuration
- Timeout and memory handling notes
- CrewAI integration pattern

# Rules
- Assume local Ollama on port 11434 unless overridden.
- Favor conservative defaults for 4GB VRAM.
- Document fallback behavior for model load or timeout issues.

# Example
/ollama-runtime
Input: Configure deepseek-r1:7b on RTX 3050 4GB for CrewAI.
