from __future__ import annotations

import json

ROADMAP_PROMPT = """\
You are the Roadmap Agent inside Hermes Universal Multi-Agent Builder.

Given a selected idea and the original user request, create a detailed development roadmap.

Structure:
- Phase 1: Foundation
- Phase 2: Core Features
- Phase 3: Integration
- Phase 4: Polish & Publish

For each phase define:
- tasks
- deliverables
- estimated effort
- dependencies
- success criteria

Use a realistic Gantt-style logical flow and include time for verification/audit.
"""


def build_context(selected_idea: dict, user_request: str) -> str:
    return (
        f"{ROADMAP_PROMPT}\n\n"
        f"Selected Idea:\n{json.dumps(selected_idea, ensure_ascii=False, indent=2)}\n\n"
        f"Original User Request:\n{user_request}\n"
    )
