"""Executor utilities for the Universal Multi-Agent Builder.

This module intentionally does NOT call ``delegate_task`` directly.
``delegate_task`` is a tool only available inside an active Hermes agent
runtime.  Instead, this module prepares focused prompts/contexts that an
orchestrating agent or skill can submit to ``delegate_task`` or a child
agent session.
"""

from __future__ import annotations

from multi_agent_builder.orchestrator import BuilderOrchestrator
from multi_agent_builder.schemas import BuildState
from multi_agent_builder.agents import (
    architect,
    auditor,
    builder as builder_agent,
    github as github_agent,
    planner,
    recommender,
    roadmap as roadmap_agent,
    verifier,
)


def prepare_recommender_context(user_request: str) -> str:
    return recommender.build_context(user_request)


def prepare_roadmap_context(state: BuildState) -> str:
    if state.selected_idea is None:
        raise ValueError("selected_idea is required before roadmap context")
    return roadmap_agent.build_context(state.selected_idea.model_dump(), state.user_request)


def prepare_architect_context(state: BuildState) -> str:
    if state.selected_idea is None or not state.roadmap:
        raise ValueError("selected_idea and roadmap are required before architect context")
    return architect.build_context(
        state.selected_idea.model_dump(),
        [phase.model_dump() for phase in state.roadmap],
    )


def prepare_planner_context(state: BuildState) -> str:
    if state.architecture is None:
        raise ValueError("architecture is required before planner context")
    return planner.build_context(state.architecture.model_dump())


def prepare_builder_context(state: BuildState) -> str:
    if not state.plan:
        raise ValueError("plan is required before builder context")
    return builder_agent.build_context(
        [spec.model_dump() for spec in state.plan],
        state.architecture.model_dump() if state.architecture else {},
    )


def prepare_verifier_context(state: BuildState) -> str:
    if not state.plan or not state.code:
        raise ValueError("plan and code are required before verifier context")
    return verifier.build_context(
        [spec.model_dump() for spec in state.plan],
        state.code,
    )


def prepare_auditor_context(state: BuildState) -> str:
    if not state.code or state.architecture is None:
        raise ValueError("code and architecture are required before auditor context")
    return auditor.build_context(state.code, state.architecture.model_dump())


def prepare_github_context(
    state: BuildState,
    repo_config: dict,
    github_repo_url: str,
) -> str:
    if state.audit is None:
        raise ValueError("audit is required before github context")
    return github_agent.build_context(
        state.code,
        state.audit,
        repo_config,
        github_repo_url,
    )


def build_sequential_contexts(user_request: str) -> dict[str, str]:
    """Return a lightweight context map for all builder stages."""
    orch = BuilderOrchestrator(user_request)
    state = orch.state
    return {
        "recommender": prepare_recommender_context(user_request),
        "roadmap": state.selected_idea and prepare_roadmap_context(state),
        "architect": state.architecture and prepare_architect_context(state),
        "planner": state.architecture and prepare_planner_context(state),
        "builder": state.plan and prepare_builder_context(state),
        "verifier": state.code and prepare_verifier_context(state),
        "auditor": state.code and prepare_auditor_context(state),
    }
