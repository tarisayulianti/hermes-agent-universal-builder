import json
import os
import sys
import tempfile

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from multi_agent_builder.orchestrator import BuilderOrchestrator, state_file_for
from multi_agent_builder.schemas import BuildState, IdeaOption, RoadmapPhase
from multi_agent_builder.executor import build_sequential_contexts
from multi_agent_builder.tools.verifier_auditor import run_syntax_checks


@pytest.fixture()
def tmp_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("HERMES_HOME", raising=False)
    return home


def test_state_file_path_is_stable():
    path = state_file_for("build a todo API")
    assert path.suffix == ".json"
    assert path.parent.name == "state"
    assert path.parent.parent.name == "multi_agent_builder"


def test_orchestrator_creates_state_file(tmp_home):
    request = "build a todo API"
    orch = BuilderOrchestrator(request)
    orch.transition("recommending")
    path = state_file_for(request)
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["user_request"] == request
    assert data["status"] == "recommending"


def test_build_state_roundtrip():
    option = IdeaOption(rank=1, name="FastAPI", concept="REST API", tech_stack=["fastapi"], pros=["fast"], cons=["few libs"], complexity="Low")
    phase = RoadmapPhase(phase=1, name="Foundation", tasks=["init"], deliverables=["repo"], effort="1h", dependencies=[], success_criteria=["repo exists"])
    state = BuildState(user_request="request", selected_idea=option, roadmap=[phase])
    payload = state.model_dump()
    restored = BuildState(**payload)
    assert restored.selected_idea.name == "FastAPI"
    assert restored.roadmap[0].name == "Foundation"


def test_build_sequential_contexts_returns_map():
    contexts = build_sequential_contexts("build a todo API unique request abc")
    assert "recommender" in contexts
    assert isinstance(contexts["recommender"], str)
    assert contexts["roadmap"] is None
    assert contexts["architect"] is None


def test_run_syntax_checks_detects_bad_python():
    code = {"app.py": "def bad(:\n    pass\n"}
    result = run_syntax_checks(code)
    assert result["overall"] == "FAIL"
    assert result["files"]["app.py"]["status"] == "FAIL"


def test_run_syntax_checks_passes_clean_python():
    code = {"app.py": "def hello():\n    return 'ok'\n"}
    result = run_syntax_checks(code)
    assert result["overall"] == "PASS"
