from __future__ import annotations

import json
from typing import Any

from multi_agent_builder.orchestrator import BuilderOrchestrator
from multi_agent_builder.schemas import BuildState


MAX_RETRIES = 3


def run_pipeline(
    user_request: str,
    auto_select: bool = False,
    github_repo_url: str | None = None,
) -> BuildState:
    orch = BuilderOrchestrator(user_request)
    state = orch.state

    try:
        orch.transition("recommending")
        # Stage 1: recommend
        from multi_agent_builder.agents import recommender

        recommender_context = recommender.build_context(user_request)
        # The actual agent execution is performed by Hermes delegate_task.
        # Here we keep the pipeline contract stable and ready for wiring.
        state.roadmap = []
        state.architecture = None
        state.plan = []
        state.code = {}
        state.verification = None
        state.audit = None
        state.github_url = None
        state.status = "idle"
        orch.save_state(state)
        return state
    except Exception as exc:
        orch.transition("failed")
        raise RuntimeError(f"Pipeline initialization failed: {exc}") from exc
