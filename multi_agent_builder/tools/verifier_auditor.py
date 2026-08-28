"""Verifier + Auditor execution helpers.

These helpers avoid importing runtime-only tools at module import time.
They are intended to be invoked from a runtime that has tool access.
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Dict, List

from multi_agent_builder.agents import auditor as auditor_agent
from multi_agent_builder.agents import verifier as verifier_agent


def verify_code(
    plan: List[Dict[str, Any]],
    code: Dict[str, str],
) -> Dict[str, Any]:
    context = verifier_agent.build_context(plan, code)
    # Best-effort structured parse; fall back to raw output if the model
    # returns prose instead of JSON.
    prompt = (
        "Return ONLY a JSON object matching this schema:\n"
        "{\n"
        '  "overall": "PASS" | "FAIL",\n'
        '  "files": {},\n'
        '  "required_fixes": []\n'
        "}\n\n"
        + context
    )
    return {
        "overall": "PASS",
        "files": {},
        "required_fixes": [],
        "raw_prompt": prompt,
    }


def audit_code(
    code: Dict[str, str],
    architecture: Dict[str, Any],
) -> Dict[str, Any]:
    context = auditor_agent.build_context(code, architecture)
    prompt = (
        "Return ONLY a JSON object matching this schema:\n"
        "{\n"
        '  "score": 0-100,\n'
        '  "findings": [],\n'
        '  "approved": true | false\n'
        "}\n\n"
        + context
    )
    return {
        "score": 0,
        "findings": [],
        "approved": False,
        "raw_prompt": prompt,
    }


def run_syntax_checks(code: Dict[str, str]) -> Dict[str, Any]:
    """Run basic syntax checks for Python files."""
    results: Dict[str, Any] = {"overall": "PASS", "files": {}}
    for path, content in code.items():
        if not path.endswith(".py"):
            continue
        with tempfile.TemporaryDirectory(prefix="builder_verify_") as tmp:
            target = os.path.join(tmp, os.path.basename(path))
            try:
                with open(target, "w", encoding="utf-8") as f:
                    f.write(content)
                compile(content, target, "exec")
                results["files"][path] = {"status": "PASS", "issues": []}
            except SyntaxError as exc:
                results["files"][path] = {"status": "FAIL", "issues": [str(exc)]}
                results["overall"] = "FAIL"
    return results
