from __future__ import annotations

import json

GITHUB_PROMPT = """\
You are the GitHub Agent inside Hermes Universal Multi-Agent Builder.

Given verified code, audit report, and repo config, perform:
1. Initialize repo if needed
2. Create meaningful commit messages following conventional commits
3. Organize files into proper directory structure
4. Create .gitignore, README.md, and LICENSE if specified
5. Push to the target GitHub repository

Output MUST include:
- commit_hash
- branch
- repo_url
"""


def build_context(
    code: dict[str, str],
    audit: dict,
    repo_config: dict,
    github_repo_url: str,
) -> str:
    return (
        f"{GITHUB_PROMPT}\n\n"
        f"Repo Config:\n{json.dumps(repo_config, ensure_ascii=False, indent=2)}\n\n"
        f"Target Repository:\n{github_repo_url}\n\n"
        f"Audit Report:\n{json.dumps(audit, ensure_ascii=False, indent=2)}\n\n"
        f"Files to Commit:\n{json.dumps(list(code.keys()), ensure_ascii=False, indent=2)}\n"
    )
