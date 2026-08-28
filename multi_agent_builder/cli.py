"""Entry point for ``python -m multi_agent_builder``."""

from __future__ import annotations

import argparse
import json
import sys

from multi_agent_builder.orchestrator import BuilderOrchestrator, state_file_for
from multi_agent_builder.pipeline import run_pipeline
from multi_agent_builder.schemas import BuildState
from multi_agent_builder.executor import build_sequential_contexts


def _print_state(state: BuildState) -> None:
    print(json.dumps(state.model_dump(), indent=2, ensure_ascii=False))


def cmd_run(args: argparse.Namespace) -> int:
    request = args.request
    auto = args.auto
    repo = args.repo

    orch = BuilderOrchestrator(request)
    orch.transition("recommending")
    state = run_pipeline(request, auto_select=auto, github_repo_url=repo)

    print(f"[builder] request: {state.user_request}")
    print(f"[builder] status: {state.status}")
    print(f"[builder] state_file: {state_file_for(request)}")
    _print_state(state)
    return 0


def cmd_contexts(args: argparse.Namespace) -> int:
    request = args.request
    try:
        contexts = build_sequential_contexts(request)
    except Exception as exc:
        print(f"[builder] context preparation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(contexts, indent=2, ensure_ascii=False))
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    request = args.request
    state = BuilderOrchestrator(request).state
    _print_state(state)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    request = args.request
    path = state_file_for(request)
    if not path.exists():
        print(f"No build state found for: {request}")
        return 1
    state = BuilderOrchestrator(request).state
    print(f"request: {state.user_request}")
    print(f"status: {state.status}")
    print(f"state_file: {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="multi_agent_builder.cli",
        description="Hermes Universal Multi-Agent Builder CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run builder pipeline for a request")
    run_parser.add_argument("request", help="User request to build")
    run_parser.add_argument("--auto", action="store_true", help="Auto-select first recommendation")
    run_parser.add_argument("--repo", help="Target GitHub repo URL")

    ctx_parser = subparsers.add_parser("contexts", help="Show prepared agent contexts for a request")
    ctx_parser.add_argument("request", help="User request")

    resume_parser = subparsers.add_parser("resume", help="Show current build state")
    resume_parser.add_argument("request", help="User request")

    status_parser = subparsers.add_parser("status", help="Show build state file path and status")
    status_parser.add_argument("request", help="User request")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return cmd_run(args)
    if args.command == "contexts":
        return cmd_contexts(args)
    if args.command == "resume":
        return cmd_resume(args)
    if args.command == "status":
        return cmd_status(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
