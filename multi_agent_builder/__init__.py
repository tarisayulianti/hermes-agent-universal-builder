from multi_agent_builder.schemas import BuildState
from multi_agent_builder.orchestrator import BuilderOrchestrator

try:
    from multi_agent_builder.pipeline import run_pipeline
except ImportError:
    def run_pipeline(*args, **kwargs):  # type: ignore[misc]
        raise ImportError("multi_agent_builder.pipeline failed to import; check agent submodules.")

try:
    from multi_agent_builder.executor import build_sequential_contexts
except ImportError:
    def build_sequential_contexts(*args, **kwargs):  # type: ignore[misc]
        raise ImportError("multi_agent_builder.executor failed to import.")

try:
    from multi_agent_builder.tools import run_github_agent, verify_code, audit_code, run_syntax_checks
except ImportError:
    def run_github_agent(*args, **kwargs):  # type: ignore[misc]
        raise ImportError("multi_agent_builder.tools failed to import.")
    def verify_code(*args, **kwargs):  # type: ignore[misc]
        raise ImportError("multi_agent_builder.tools failed to import.")
    def audit_code(*args, **kwargs):  # type: ignore[misc]
        raise ImportError("multi_agent_builder.tools failed to import.")
    def run_syntax_checks(*args, **kwargs):  # type: ignore[misc]
        raise ImportError("multi_agent_builder.tools failed to import.")

__all__ = [
    "BuildState",
    "BuilderOrchestrator",
    "run_pipeline",
    "build_sequential_contexts",
    "run_github_agent",
    "verify_code",
    "audit_code",
    "run_syntax_checks",
]
