from __future__ import annotations

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from .schemas import BuildState


def _state_home() -> Path:
    base = Path.home() / ".hermes" / "multi_agent_builder" / "state"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _request_hash(user_request: str) -> str:
    return hashlib.sha256(user_request.encode("utf-8")).hexdigest()[:16]


def state_file_for(user_request: str) -> Path:
    return _state_home() / f"{_request_hash(user_request)}.json"


def load_state(user_request: str) -> BuildState:
    path = state_file_for(user_request)
    if not path.exists():
        return BuildState(user_request=user_request)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return BuildState(**data)
    except Exception:
        return BuildState(user_request=user_request)


def save_state(state: BuildState) -> Path:
    path = state_file_for(state.user_request)
    payload = state.model_dump()
    payload["_updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


class BuilderOrchestrator:
    def __init__(self, user_request: str) -> None:
        self.state = load_state(user_request)
        self.user_request = user_request

    def update(self, **changes: Any) -> None:
        for key, value in changes.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        save_state(self.state)

    def transition(self, status: str) -> None:
        self.update(status=status)

    def save_state(self, state: BuildState) -> None:
        save_state(state)

    def current_context(self) -> dict[str, Any]:
        return self.state.model_dump()
