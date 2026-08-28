"""Abstractions for executing builder stages inside a live Hermes runtime.

This module intentionally avoids importing runtime-only tools such as
``delegate_task`` at module import time.  Instead it exposes thin callables
that an orchestrator, skill, or runtime can bind to the real tool surface
when needed.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class DelegateTaskInvoker(Protocol):
    def __call__(
        self,
        goal: str,
        context: Optional[str] = None,
        role: Optional[str] = None,
        output_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        ...


@runtime_checkable
class GitHubAgentExecutor(Protocol):
    def __call__(
        self,
        code: Dict[str, str],
        audit: Dict[str, Any],
        repo_config: Dict[str, Any],
        github_repo_url: str,
    ) -> Dict[str, Any]:
        ...


@runtime_checkable
class VerifierExecutor(Protocol):
    def __call__(
        self,
        plan: List[Dict[str, Any]],
        code: Dict[str, str],
    ) -> Dict[str, Any]:
        ...


@runtime_checkable
class AuditorExecutor(Protocol):
    def __call__(
        self,
        code: Dict[str, str],
        architecture: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...


class RuntimeBindings:
    """Container for optional runtime bindings.

    If a binding is missing, the corresponding pipeline stage can be skipped
    or routed through a manual/CLI fallback path.
    """

    def __init__(
        self,
        delegate_task: Optional[DelegateTaskInvoker] = None,
        github: Optional[GitHubAgentExecutor] = None,
        verifier: Optional[VerifierExecutor] = None,
        auditor: Optional[AuditorExecutor] = None,
        terminal: Optional[Any] = None,
        write_file: Optional[Any] = None,
    ) -> None:
        self.delegate_task = delegate_task
        self.github = github
        self.verifier = verifier
        self.auditor = auditor
        self.terminal = terminal
        self.write_file = write_file

    def delegate(self, context: str, role: str = "leaf") -> str:
        if self.delegate_task is None:
            raise RuntimeError(
                "delegate_task binding is required for live runtime execution. "
                "Pass a real invoker when wiring this pipeline inside Hermes."
            )
        return self.delegate_task(goal=context, role=role)
