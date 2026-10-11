---
name: project-builder
description: Bootstrap a brand-new project from a raw brief (assignment, methodology doc, idea) into a structured, documented skeleton, by dispatching the project-builder agent.
disable-model-invocation: true
---

Dispatch the `project-builder` agent (Agent tool, `subagent_type: "project-builder"`) to bootstrap a new project from the brief given in ARGUMENTS.

If ARGUMENTS is empty or too thin to work from (no brief, methodology, or idea described), ask the user for the project brief before dispatching — never invoke the agent with nothing to build from.

Otherwise, call the Agent tool now with:
- `subagent_type`: `"project-builder"`
- `description`: a short (3-6 word) summary of what's being bootstrapped
- `prompt`: the full brief from ARGUMENTS, verbatim, plus the current working directory so the agent knows where to write files

After dispatching, tell the user the agent is running and that it will ask them questions directly (via `AskUserQuestion`) as it works through the grilling → domain-modeling → spec → tickets pipeline — that's expected, not an error.
