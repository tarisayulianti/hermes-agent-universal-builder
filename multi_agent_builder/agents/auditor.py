from __future__ import annotations

import json

AUDITOR_PROMPT = """\
You are the Auditor Agent inside Hermes Universal Multi-Agent Builder.

Given code output and architecture, perform a comprehensive audit:
1. Security vulnerabilities: SQL injection, XSS, secrets exposure, etc.
2. Performance bottlenecks
3. Code smells & anti-patterns
4. Test coverage adequacy
5. Documentation completeness
6. License compliance for dependencies

Output MUST be a JSON object:
{
  "score": 0-100,
  "findings": [
    {
      "level": "critical" | "medium" | "low",
      "category": "...",
      "location": "...",
      "issue": "...",
      "remediation": "..."
    }
  ],
  "approved": true | false
}
"""


def build_context(code: dict[str, str], architecture: dict) -> str:
    return (
        f"{AUDITOR_PROMPT}\n\n"
        f"Architecture:\n{json.dumps(architecture, ensure_ascii=False, indent=2)}\n\n"
        f"Code Output:\n{json.dumps(code, ensure_ascii=False, indent=2)}\n"
    )
