"""Runtime executor for the Universal Multi-Agent Builder.

This module is designed to be called from WITHIN an active Hermes agent session.
It does NOT import `delegate_task` at module level. Instead, it provides:

- `execute_stage(stage, state, runtime_bindings)` — run one pipeline stage
- `run_pipeline_live(user_request, runtime_bindings)` — run the full 8-stage pipeline
- Context builders that call `runtime_bindings.delegate(...)` when available

Usage from a skill/agent:
  from multi_agent_builder.runtime_executor import run_pipeline_live
  result = run_pipeline_live("build a todo API", bindings)
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from multi_agent_builder.orchestrator import BuilderOrchestrator
from multi_agent_builder.schemas import BuildState, ArchitectureDoc, FileSpec, IdeaOption, RoadmapPhase
from multi_agent_builder.executor import (
    build_sequential_contexts,
    prepare_recommender_context,
    prepare_roadmap_context,
    prepare_architect_context,
    prepare_planner_context,
    prepare_builder_context,
    prepare_verifier_context,
    prepare_auditor_context,
    prepare_github_context,
)
from multi_agent_builder.runtime import RuntimeBindings
from multi_agent_builder.tools.github_agent import run_github_agent


def _extract_json_array(text: str) -> list[dict]:
    """Best-effort extract first JSON array from text."""
    start = text.find('[')
    end = text.rfind(']')
    if start == -1 or end == -1:
        raise ValueError("No JSON array found in recommender output")
    return json.loads(text[start:end + 1])


def _extract_json_object(text: str) -> dict:
    """Best-effort extract first JSON object from text."""
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in output")
    return json.loads(text[start:end + 1])


def execute_stage(
    stage: str,
    state: BuildState,
    runtime: RuntimeBindings,
) -> Dict[str, Any]:
    """Execute a single pipeline stage.

    Stages: recommender, roadmap, architect, planner, builder, verifier, auditor, github
    """
    if stage == "recommender":
        context = prepare_recommender_context(state.user_request)
        result_text = runtime.delegate(context, role="leaf")
        ideas = _extract_json_array(result_text)
        state.selected_idea = IdeaOption(**ideas[0])
        state.status = "recommending"
        return {"ideas": ideas, "selected": state.selected_idea.model_dump()}

    if stage == "roadmap":
        if state.selected_idea is None:
            raise ValueError("selected_idea required before roadmap")
        context = prepare_roadmap_context(state)
        result_text = runtime.delegate(context, role="leaf")
        roadmap_data = _extract_json_object(result_text)
        state.roadmap = [RoadmapPhase(**phase) for phase in roadmap_data.get("phases", [])]
        state.status = "planning"
        return {"roadmap": [p.model_dump() for p in state.roadmap]}

    if stage == "architect":
        if state.selected_idea is None or not state.roadmap:
            raise ValueError("selected_idea and roadmap required before architect")
        context = prepare_architect_context(state)
        result_text = runtime.delegate(context, role="leaf")
        arch_data = _extract_json_object(result_text)
        state.architecture = ArchitectureDoc(**arch_data)
        state.status = "planning"
        return {"architecture": state.architecture.model_dump()}

    if stage == "planner":
        if state.architecture is None:
            raise ValueError("architecture required before planner")
        context = prepare_planner_context(state)
        result_text = runtime.delegate(context, role="leaf")
        plan_data = _extract_json_object(result_text)
        state.plan = [FileSpec(**item) for item in plan_data.get("files", [])]
        state.status = "planning"
        return {"plan": [p.model_dump() for p in state.plan]}

    if stage == "builder":
        if not state.plan or not state.architecture:
            raise ValueError("plan and architecture required before builder")
        context = prepare_builder_context(state)
        result_text = runtime.delegate(context, role="leaf")
        code_data = _extract_json_object(result_text)
        state.code = code_data.get("files", {})
        state.status = "building"
        return {"code": state.code}

    if stage == "verifier":
        if not state.plan or not state.code:
            raise ValueError("plan and code required before verifier")
        context = prepare_verifier_context(state)
        result_text = runtime.delegate(context, role="leaf")
        verification = _extract_json_object(result_text)
        state.verification = verification
        state.status = "verifying"
        return {"verification": state.verification}

    if stage == "auditor":
        if not state.code or not state.architecture:
            raise ValueError("code and architecture required before auditor")
        context = prepare_auditor_context(state)
        result_text = runtime.delegate(context, role="leaf")
        audit = _extract_json_object(result_text)
        state.audit = audit
        state.status = "auditing"
        return {"audit": state.audit}

    if stage == "github":
        if state.code is None or state.audit is None:
            raise ValueError("code and audit required before github")
        repo_url = state.github_url or os.getenv("BUILDER_GITHUB_REPO", "")
        if not repo_url:
            raise ValueError("github_repo_url required for github stage")
        report = run_github_agent(
            state=state,
            repo_config={},
            github_repo_url=repo_url,
            terminal=runtime.terminal,
            write_file=runtime.write_file,
        )
        state.github_url = report.get("repo_url")
        state.status = "done" if report.get("ok") else "failed"
        return {"github": report}

    raise ValueError(f"Unknown stage: {stage}")


def run_pipeline_live(
    user_request: str,
    runtime: RuntimeBindings,
    auto_select: bool = False,
    github_repo_url: Optional[str] = None,
    max_retries: int = 3,
) -> BuildState:
    """Run the full 8-stage pipeline using live runtime bindings."""
    orch = BuilderOrchestrator(user_request)
    state = orch.state
    if github_repo_url:
        state.github_url = github_repo_url

    stages = [
        "recommender",
        "roadmap",
        "architect",
        "planner",
        "builder",
        "verifier",
        "auditor",
        "github",
    ]

    index = 0
    retry_count = 0
    while index < len(stages):
        stage = stages[index]
        orch.transition(stage)

        if stage in ("verifier", "auditor") and retry_count >= max_retries:
            state.status = "failed"
            orch.save_state(state)
            return state

        try:
            execute_stage(stage, state, runtime)
            retry_count = 0
            index += 1
        except ValueError as exc:
            if stage in ("verifier", "auditor"):
                retry_count += 1
                state.retry_count = retry_count
                orch.save_state(state)
                if retry_count >= max_retries:
                    state.status = "failed"
                    orch.save_state(state)
                    return state
                index = stages.index("builder")
            else:
                state.status = "failed"
                orch.save_state(state)
                return state

    state.status = "done"
    orch.save_state(state)
    return state
