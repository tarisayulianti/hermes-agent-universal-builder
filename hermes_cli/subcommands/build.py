"""``hermes build`` subcommand parser.

Mirrors the style of ``hermes_cli/subcommands/cron.py`` and ``setup.py``:
- parser builder only
- avoids importing ``main`` to prevent cycles
"""

from __future__ import annotations

from typing import Callable


def _run_build(args) -> int:
    from multi_agent_builder.cli import main as _builder_main

    argv = [getattr(args, "request", "")]
    if getattr(args, "auto", False):
        argv.append("--auto")
    repo = getattr(args, "repo", None)
    if repo:
        argv += ["--repo", repo]
    if getattr(args, "resume", False):
        argv.append("--resume")
    return _builder_main(argv)


def build_build_parser(subparsers, *, cmd_build: Callable) -> None:
    """Attach the ``build`` subcommand to ``subparsers``."""
    build_parser = subparsers.add_parser(
        "build",
        help="Run the Universal Multi-Agent Builder pipeline",
        description=(
            "Translate a user request into a complete project through the "
            "multi-agent pipeline: recommend → roadmap → architecture → plan → "
            "build → verify → audit → github."
        ),
    )
    build_parser.add_argument(
        "request",
        help="Natural-language project request, e.g. 'FastAPI auth service with JWT'",
    )
    build_parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-select the top recommendation without user confirmation",
    )
    build_parser.add_argument(
        "--repo",
        help="Target GitHub repository URL to push the generated project",
    )
    build_parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume an existing build state for the same request instead of starting over",
    )
    build_parser.set_defaults(func=cmd_build)
