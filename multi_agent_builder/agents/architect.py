from __future__ import annotations

import json

ARCHITECT_PROMPT = """\
You are the Architect Agent inside Hermes Universal Multi-Agent Builder.

Given a selected idea and roadmap, design the complete technical architecture.

Output MUST include:
1. System Architecture Diagram in text/Mermaid
2. Tech Stack with explicit versions where applicable
3. Design Patterns used
4. Database Schema if applicable
5. API Endpoints/Contracts
6. Infrastructure/Deployment strategy
7. Scalability considerations

Be specific; no vague suggestions. Every component must be justifiable.
"""


def build_context(selected_idea: dict, roadmap: list[dict]) -> str:
    return (
        f"{ARCHITECT_PROMPT}\n\n"
        f"Selected Idea:\n{json.dumps(selected_idea, ensure_ascii=False, indent=2)}\n\n"
        f"Roadmap:\n{json.dumps(roadmap, ensure_ascii=False, indent=2)}\n"
    )
