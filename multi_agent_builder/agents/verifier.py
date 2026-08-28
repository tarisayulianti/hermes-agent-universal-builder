from __future__ import annotations

import json

VERIFIER_PROMPT = """\
You are the Verifier Agent inside Hermes Universal Multi-Agent Builder.

Given the plan and generated code, verify:
1. Does every file in the plan exist in the code output?
2. Is every function implemented with no stubs?
3. Is the syntax valid for the target language?
4. Do function signatures match the plan?
5. Are all imports resolvable?
6. Is there any obvious runtime error?

Output MUST be a JSON object:
{
  "overall": "PASS" | "FAIL",
  "files": {
    "<path>": {
      "status": "PASS" | "FAIL",
      "issues": ["..."]
    }
  },
  "required_fixes": ["..."]
}
"""


def build_context(plan: list[dict], code: dict[str, str]) -> str:
    return (
        f"{VERIFIER_PROMPT}\n\n"
        f"Plan:\n{json.dumps(plan, ensure_ascii=False, indent=2)}\n\n"
        f"Code Output:\n{json.dumps(code, ensure_ascii=False, indent=2)}\n"
    )
