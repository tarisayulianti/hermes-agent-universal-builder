from pydantic import BaseModel, Field, model_validator
from typing import Literal, List, Optional, Dict, Any


class IdeaOption(BaseModel):
    rank: int
    name: str
    concept: str
    tech_stack: List[str]
    pros: List[str]
    cons: List[str]
    complexity: Literal["Low", "Medium", "High"]


class RoadmapPhase(BaseModel):
    phase: int
    name: str
    tasks: List[str]
    deliverables: List[str]
    effort: str
    dependencies: List[str]
    success_criteria: List[str]


class ArchitectureDoc(BaseModel):
    diagram_text: Optional[str] = ""
    tech_stack: Dict[str, str] = {}
    design_patterns: List[str] = []
    db_schema: Optional[str] = None
    api_endpoints: List[str] = []
    deployment: str = ""
    scalability: str = ""


class FileFunctionSpec(BaseModel):
    name: str
    signature: str
    description: str
    dependencies: List[str] = []


class FileSpec(BaseModel):
    path: str
    purpose: str
    functions: List[FileFunctionSpec]
    tests: str


class BuildState(BaseModel):
    user_request: str
    selected_idea: Optional[IdeaOption] = None
    roadmap: List[RoadmapPhase] = []
    architecture: Optional[ArchitectureDoc] = None
    plan: List[FileSpec] = []
    code: Dict[str, str] = {}
    verification: Optional[Dict[str, Any]] = None
    audit: Optional[Dict[str, Any]] = None
    github_url: Optional[str] = None
    retry_count: int = 0
    status: Literal[
        "idle",
        "recommending",
        "planning",
        "building",
        "verifying",
        "auditing",
        "shipping",
        "done",
        "failed",
        "aborted",
    ] = "idle"

    @model_validator(mode="before")
    @classmethod
    def coerce_model_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if data.get("selected_idea") and isinstance(data["selected_idea"], dict):
            data["selected_idea"] = IdeaOption(**data["selected_idea"])
        if data.get("roadmap") and isinstance(data["roadmap"], list):
            data["roadmap"] = [
                RoadmapPhase(**item) if isinstance(item, dict) else item
                for item in data["roadmap"]
            ]
        if data.get("architecture") and isinstance(data["architecture"], dict):
            data["architecture"] = ArchitectureDoc(**data["architecture"])
        if data.get("plan") and isinstance(data["plan"], list):
            data["plan"] = [
                FileSpec(**item) if isinstance(item, dict) else item
                for item in data["plan"]
            ]
        return data
