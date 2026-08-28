"""Phase 4 Live Demo: end-to-end pipeline run with valid schema data.

This script demonstrates the exact binding pattern an active Hermes agent
must use to call the builder pipeline from a skill/turn. It uses `FakeDelegateTask`
to stand in for the real `delegate_task` tool, but the binding shape, stage order,
state transitions, and JSON extraction are identical to a live run.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from multi_agent_builder.runtime import RuntimeBindings
from multi_agent_builder.runtime_executor import run_pipeline_live


class FakeDelegateTask:
    """Mimics Hermes `delegate_task` returning schema-valid JSON per stage."""

    STAGE_RESULTS = {
        "recommender": json.dumps([
            {
                "rank": 1,
                "name": "FastAPI + SQLite",
                "concept": "Lightweight REST API",
                "tech_stack": ["FastAPI", "SQLite"],
                "pros": ["Fast"],
                "cons": ["None"],
                "complexity": "Low",
            }
        ]),
        "roadmap": json.dumps({
            "phases": [
                {
                    "phase": 1,
                    "name": "Foundation",
                    "tasks": ["Setup project"],
                    "deliverables": ["Scaffold"],
                    "effort": "1 day",
                    "dependencies": [],
                    "success_criteria": ["Repo initialized"],
                }
            ]
        }),
        "architect": json.dumps({
            "diagram_text": "Client -> FastAPI -> SQLite",
            "tech_stack": {"backend": "FastAPI 0.104+", "db": "SQLite 3"},
            "design_patterns": ["Repository"],
            "db_schema": "CREATE TABLE todos (...);",
            "api_endpoints": ["/todos"],
            "deployment": "Uvicorn",
            "scalability": "Single-node",
        }),
        "planner": json.dumps({
            "files": [
                {
                    "path": "app/main.py",
                    "purpose": "FastAPI app entrypoint",
                    "functions": [
                        {"name": "create_app", "signature": "()", "description": "Build app", "dependencies": []}
                    ],
                    "tests": "pytest",
                }
            ]
        }),
        "builder": json.dumps({
            "files": {
                "app/main.py": "from fastapi import FastAPI\napp = FastAPI()"
            }
        }),
        "verifier": json.dumps({"overall": "PASS", "files": {"app/main.py": "PASS"}, "required_fixes": []}),
        "auditor": json.dumps({"score": 90, "findings": [], "approved": True}),
    }

    def __call__(self, goal: str, context: str | None = None, role: str | None = None, output_schema: dict | None = None) -> str:
        text = goal.lower()
        if "github agent" in text:
            stage = "github"
        elif "auditor agent" in text:
            stage = "auditor"
        elif "verifier agent" in text:
            stage = "verifier"
        elif "builder agent" in text:
            stage = "builder"
        elif "planner agent" in text:
            stage = "planner"
        elif "architect agent" in text:
            stage = "architect"
        elif "roadmap agent" in text:
            stage = "roadmap"
        elif "recommender agent" in text or "recommend" in text:
            stage = "recommender"
        else:
            stage = "recommender"
        return self.STAGE_RESULTS[stage]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="builder-demo-") as workdir:
        bindings = RuntimeBindings(
            delegate_task=FakeDelegateTask(),
            terminal=lambda **kwargs: {"output": "", "error": "", "exit_code": 0},
            write_file=lambda path, content: Path(path).write_text(content, encoding="utf-8"),
        )
        state = run_pipeline_live(
            "Phase 4 live demo: build a todo API",
            bindings,
            auto_select=True,
            github_repo_url="https://github.com/tarisayulianti/hermes-agent-universal-builder.git",
        )
        print(f"status={state.status}")
        print(f"selected_idea={state.selected_idea.name if state.selected_idea else None}")
        print(f"roadmap_phases={len(state.roadmap)}")
        print(f"architecture_tech_stack={state.architecture.tech_stack if state.architecture else None}")
        print(f"plan_files={len(state.plan)}")
        print(f"code_files={len(state.code)}")
        print(f"verification={state.verification}")
        print(f"audit_score={state.audit.get('score') if state.audit else None}")
        print(f"github_url={state.github_url}")

        assert state.status in {"done", "failed"}
        assert state.selected_idea is not None
        assert state.architecture is not None
        assert len(state.plan) > 0
        assert len(state.code) > 0
        assert state.verification is not None
        assert state.audit is not None
        print("Phase 4 demo assertions passed")


if __name__ == "__main__":
    main()
