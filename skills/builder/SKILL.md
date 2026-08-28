---
name: builder
description: "Universal multi-agent builder: idea to GitHub."
metadata:
  hermes:
    tags: [builder, multi-agent, scaffolding, github, codegen]
---

# Builder Skill

Use when the user wants to build, scaffold, or generate a project from idea to GitHub.

## Prerequisites
- User request: natural-language project description
- Optional: `--repo` target GitHub repository URL
- Optional: `--auto` to skip recommendation confirmation

## Runtime Execution Model
This pipeline runs inside a live Hermes agent session. Each stage is executed
via `delegate_task`, which spawns isolated child agents with focused prompts.
The parent maintains state in `~/.hermes/multi_agent_builder/state/{hash}.json`.

**IMPORTANT**: `delegate_task` is a Hermes runtime tool, NOT a Python function.
Do NOT import it. Call it directly in your agent loop:
```
delegate_task(goal="...", context="...", role="leaf")
```

## Pipeline Stages

### Stage 1: Recommender
```
goal: |
  You are the Recommender Agent inside Hermes Universal Multi-Agent Builder.
  Given this user request, analyze current industry trends and generate
  exactly 3 distinct solution options. For each option provide:
  - Option Name, Core Concept, Recommended Tech Stack, Pros, Cons,
    Estimated Complexity (Low/Medium/High)
  Rank them from most recommended to least.
  Return ONLY a JSON array of exactly 3 objects.
context: |
  User Request: {{user_request}}
role: leaf
```
After result: parse JSON array, present to user, await selection (or auto-select first).

### Stage 2: Roadmap
```
goal: |
  You are the Roadmap Agent. Given the selected idea and original request,
  create a detailed development roadmap with 4 phases: Foundation, Core
  Features, Integration, Polish & Publish. For each phase define tasks,
  deliverables, effort, dependencies, and success criteria.
context: |
  Selected Idea: {{selected_idea_json}}
  Original Request: {{user_request}}
role: leaf
```

### Stage 3: Architect
```
goal: |
  You are the Architect Agent. Given selected idea and roadmap, design the
  complete technical architecture including: system diagram, tech stack with
  versions, design patterns, database schema, API endpoints, deployment
  strategy, and scalability considerations.
context: |
  Selected Idea: {{selected_idea_json}}
  Roadmap: {{roadmap_json}}
role: leaf
```

### Stage 4: Planner
```
goal: |
  You are the Planner Agent. Given the architecture, generate the complete
  file structure and function specifications. Output: directory tree, per-file
  purpose, exported functions/classes with signatures, dependencies, test
  strategy, config files, and package list. Do NOT write implementation code.
context: |
  Architecture: {{architecture_json}}
role: leaf
```

### Stage 5: Builder
```
goal: |
  You are the Builder Agent. Given the plan, write COMPLETE, PRODUCTION-READY
  code for every file. Rules: NO placeholders, NO TODO comments, NO 'implement
  later'. Every function must be fully implemented with error handling and
  validation. Output complete source code for all files.
context: |
  Architecture: {{architecture_json}}
  Plan: {{plan_json}}
role: leaf
```

### Stage 6: Verifier
```
goal: |
  You are the Verifier Agent. Given plan and code, verify: all files exist,
  all functions implemented, syntax valid, signatures match, imports resolvable.
  Return ONLY JSON: {"overall": "PASS|FAIL", "files": {...}, "required_fixes": []}
context: |
  Plan: {{plan_json}}
  Code: {{code_json}}
role: leaf
```
If FAIL: loop back to Builder with `required_fixes` as feedback. Max 3 retries.

### Stage 7: Auditor
```
goal: |
  You are the Auditor Agent. Given code and architecture, audit for security
  vulnerabilities, performance issues, code smells, test coverage, documentation,
  and license compliance. Return ONLY JSON:
  {"score": 0-100, "findings": [...], "approved": true|false}
context: |
  Architecture: {{architecture_json}}
  Code: {{code_json}}
role: leaf
```
If not approved and retryable: loop back to Builder. Max 3 retries.

### Stage 8: GitHub
Use the `terminal` tool directly:
```
terminal(command="git init", workdir=<project_dir>)
terminal(command="git checkout -b main", workdir=<project_dir>)
# Write files using write_file tool
terminal(command="git add .", workdir=<project_dir>)
terminal(command="git commit -m 'chore(builder): init project'", workdir=<project_dir>)
terminal(command="git remote add origin <repo_url>", workdir=<project_dir>)
terminal(command="git push -u origin main", workdir=<project_dir>)
```

## Runtime Wiring Contract

This pipeline is designed to run from within an active Hermes agent turn.
`delegate_task` is a Hermes tool; it is not importable from ordinary helper modules.
Do not attempt to import or call `delegate_task` from `multi_agent_builder` code.

### Intended live invocation

From an active agent session, bind the real tool callables into `RuntimeBindings`
and pass that object into `run_pipeline_live(...)`. The helper module only consumes
the injected bindings; it never imports the live runtime itself.

```python
from multi_agent_builder.runtime_executor import run_pipeline_live
from multi_agent_builder.runtime import RuntimeBindings

bindings = RuntimeBindings(
    delegate_task=lambda goal, context=None, role="leaf": delegate_task(
        goal=goal,
        context=context,
        role=role,
    ),
)
state = run_pipeline_live("build a todo API", bindings)
```

## State Management
After each stage, update `~/.hermes/multi_agent_builder/state/{hash}.json`:
```python
from multi_agent_builder.orchestrator import BuilderOrchestrator
orch = BuilderOrchestrator(user_request)
orch.transition("building")
orch.update(code=generated_code)
```

## Termination Criteria
- **SUCCESS**: GitHub push complete → return repo URL + summary
- **MAX RETRY**: verifier/auditor fail after 3 retries → return error report
- **USER ABORT**: user sends cancel/interrupt → save state, exit
- **CRITICAL FAIL**: unrecoverable error → save state, report to user
