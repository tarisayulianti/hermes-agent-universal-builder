import json
import os
import sys
import types
from typing import Any, Dict

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from multi_agent_builder.schemas import BuildState, IdeaOption, RoadmapPhase
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
from multi_agent_builder.tools.verifier_auditor import run_syntax_checks, verify_code, audit_code
from multi_agent_builder.tools.github_agent import run_github_agent
from multi_agent_builder.runtime_executor import execute_stage, run_pipeline_live
from multi_agent_builder.runtime import RuntimeBindings


class FakeRuntime(RuntimeBindings):
    def delegate(self, context: str, role: str = "leaf") -> str:
        if "Recommender" in context or "Generate exactly 3" in context:
            return '[{"rank":1,"name":"FastAPI","concept":"REST API","tech_stack":["fastapi"],"pros":["fast"],"cons":["few libs"],"complexity":"Low"}]'
        if "Roadmap Agent" in context:
            return '{"phases":[{"phase":1,"name":"Foundation","tasks":["init"],"deliverables":["repo"],"effort":"1h","dependencies":[],"success_criteria":["repo exists"]}]}'
        if "Architect Agent" in context:
            return '{"tech_stack":{"backend":"fastapi"},"design_patterns":["layered"],"deployment":"docker","scalability":"horizontal"}'
        if "Planner Agent" in context:
            return '{"files":[{"path":"app/main.py","purpose":"entrypoint","functions":[],"tests":"pytest"}]}'
        if "Builder Agent" in context:
            return '{"files":{"app/main.py":"def main(): return 1"}}'
        if "Verifier Agent" in context:
            return '{"overall":"PASS","files":{},"required_fixes":[]}'
        if "Auditor Agent" in context:
            return '{"score":95,"findings":[],"approved":true}'
        raise ValueError(f"Unexpected delegate context: {context[:60]}")



def _state_with_selected_idea(user_request="request") -> BuildState:
    option = IdeaOption(
        rank=1,
        name="FastAPI",
        concept="REST API",
        tech_stack=["fastapi"],
        pros=["fast"],
        cons=["few libs"],
        complexity="Low",
    )
    return BuildState(user_request=user_request, selected_idea=option)


def test_prepare_roadmap_context_raises_without_idea():
    state = BuildState(user_request="request")
    with pytest.raises(ValueError):
        prepare_roadmap_context(state)


def test_prepare_architect_context_raises_without_roadmap():
    state = _state_with_selected_idea()
    with pytest.raises(ValueError):
        prepare_architect_context(state)


def test_prepare_planner_context_raises_without_architecture():
    state = _state_with_selected_idea()
    with pytest.raises(ValueError):
        prepare_planner_context(state)


def test_prepare_builder_context_raises_without_plan():
    state = _state_with_selected_idea()
    with pytest.raises(ValueError):
        prepare_builder_context(state)


def test_prepare_verifier_context_raises_without_code():
    option = IdeaOption(
        rank=1, name="X", concept="C", tech_stack=[], pros=[], cons=[], complexity="Low"
    )
    state = BuildState(user_request="request", selected_idea=option)
    with pytest.raises(ValueError):
        prepare_verifier_context(state)


def test_prepare_auditor_context_raises_without_audit_prereqs():
    option = IdeaOption(
        rank=1, name="X", concept="C", tech_stack=[], pros=[], cons=[], complexity="Low"
    )
    state = BuildState(user_request="request", selected_idea=option)
    with pytest.raises(ValueError):
        prepare_auditor_context(state)


def test_prepare_github_context_raises_without_audit():
    option = IdeaOption(
        rank=1, name="X", concept="C", tech_stack=[], pros=[], cons=[], complexity="Low"
    )
    state = BuildState(user_request="request", selected_idea=option)
    with pytest.raises(ValueError):
        prepare_github_context(state, repo_config={}, github_repo_url="https://example.com/repo")


def test_run_syntax_checks_mixed_files():
    code = {
        "main.py": "def ok():\n    return 1\n",
        "bad.py": "def bad(:\n    pass\n",
        "readme.md": "# title\n",
    }
    result = run_syntax_checks(code)
    assert result["overall"] == "FAIL"
    assert result["files"]["main.py"]["status"] == "PASS"
    assert result["files"]["bad.py"]["status"] == "FAIL"
    assert "readme.md" not in result["files"]


def test_verify_code_returns_stub_report():
    plan = [{"path": "main.py", "functions": []}]
    code = {"main.py": "pass\n"}
    result = verify_code(plan, code)
    assert "overall" in result
    assert "files" in result
    assert "required_fixes" in result


def test_audit_code_returns_stub_report():
    code = {"main.py": "pass\n"}
    architecture = {"tech_stack": {}}
    result = audit_code(code, architecture)
    assert "score" in result
    assert "findings" in result
    assert "approved" in result


def test_run_github_agent_writes_files_and_git_status(tmp_path):
    state = BuildState(
        user_request="build a todo API",
        code={"app/main.py": "def main():\n    return 'ok'\n"},
        audit={"approved": True},
    )
    terminal_calls: Dict[str, Any] = {}

    def fake_terminal(command: str, workdir: str = None, timeout: int = 180) -> Dict[str, Any]:
        terminal_calls[command] = True
        if command.startswith("git init"):
            return {"output": "", "error": None, "exit_code": 0}
        if command.startswith("git checkout"):
            return {"output": "", "error": None, "exit_code": 0}
        if command.startswith("git add"):
            return {"output": "", "error": None, "exit_code": 0}
        if command.startswith("git commit"):
            return {"output": "main branch commit abcdef\n", "error": None, "exit_code": 0}
        if command.startswith("git remote"):
            return {"output": "", "error": None, "exit_code": 0}
        if command.startswith("git push"):
            return {"output": "", "error": None, "exit_code": 0}
        return {"output": "", "error": "unsupported", "exit_code": 1}

    write_targets: list[str] = []

    def fake_write_file(path: str, content: str) -> Dict[str, Any]:
        write_targets.append(path)
        return {"ok": True}

    report = run_github_agent(
        state=state,
        repo_config={},
        github_repo_url="https://example.com/repo",
        terminal=fake_terminal,
        write_file=fake_write_file,
        workdir=str(tmp_path),
    )
    assert report["ok"] is True
    assert any("app/main.py" in target for target in write_targets)
    assert any(target.endswith(".gitignore") for target in write_targets)
    assert any(target.endswith("README.md") for target in write_targets)
    assert any("git commit" in key for key in terminal_calls.keys())
    assert any("git push" in key for key in terminal_calls.keys())
    assert report["commit_hash"] == "abcdef"


def test_execute_stage_recommender_populates_selected_idea():
    state = BuildState(user_request="build a todo API")
    runtime = FakeRuntime()
    result = execute_stage("recommender", state, runtime)
    assert state.selected_idea is not None
    assert state.selected_idea.name == "FastAPI"
    assert state.status == "recommending"
    assert result["selected"]["name"] == "FastAPI"


def test_run_pipeline_live_full_success(tmp_path):
    runtime = FakeRuntime()
    state = run_pipeline_live(
        "build a todo API",
        runtime,
        auto_select=True,
        github_repo_url="https://example.com/repo",
    )
    assert state.status == "done"
    assert state.selected_idea is not None
    assert state.architecture is not None
    assert state.plan is not None
    assert state.code is not None
    assert state.verification is not None
    assert state.audit is not None
    assert state.github_url == "https://example.com/repo"


def test_run_pipeline_live_aborts_without_repo(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("HERMES_HOME", raising=False)
    runtime = FakeRuntime()
    state = run_pipeline_live("build a todo API unique request xyz", runtime, auto_select=True)
    assert state.status == "failed"
