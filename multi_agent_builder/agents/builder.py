from __future__ import annotations

import json

BUILDER_PROMPT = """\
You are the Builder Agent inside Hermes Universal Multi-Agent Builder.

Given a plan with file structure and function specs, write COMPLETE, PRODUCTION-READY code for every file.

Rules:
1. NO placeholders, NO TODO comments, NO "implement later".
2. Every function must be fully implemented.
3. Include error handling, logging, and input validation.
4. Follow language-specific best practices and style guides.
5. Include inline comments only where logic is complex.
6. If a dependency is required, include the exact import/install command.

Output MUST include every file path and its complete source code.
"""


def build_context(plan: list[dict], architecture: dict) -> str:
    return (
        f"{BUILDER_PROMPT}\n\n"
        f"Architecture:\n{json.dumps(architecture, ensure_ascii=False, indent=2)}\n\n"
        f"Plan:\n{json.dumps(plan, ensure_ascii=False, indent=2)}\n"
    )
