from __future__ import annotations

import json

PLANNER_PROMPT = """\
You are the Planner Agent inside Hermes Universal Multi-Agent Builder.

Given architecture, generate the complete file structure and function specifications.

Output MUST include:
1. Complete directory tree
2. Per file: filename, purpose, exported functions/classes with signatures, dependencies, and test strategy
3. Configuration files needed
4. Package/dependency list

Every function must have a clear input/output contract.
Do not write implementation; only interfaces and specs.
"""


def build_context(architecture: dict) -> str:
    return f"{PLANNER_PROMPT}\n\nArchitecture:\n{json.dumps(architecture, ensure_ascii=False, indent=2)}\n"
