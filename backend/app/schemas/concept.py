from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import Difficulty

_DIFF_MAP = {
    "basic": "BEGINNER", "easy": "BEGINNER", "beginner": "BEGINNER",
    "medium": "INTERMEDIATE", "moderate": "INTERMEDIATE", "intermediate": "INTERMEDIATE",
    "hard": "ADVANCED", "difficult": "ADVANCED", "advanced": "ADVANCED",
}


def _norm_diff(v):
    if isinstance(v, str):
        k = v.strip().lower()
        return _DIFF_MAP.get(k, k.upper())
    return v


class ConceptRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ConceptCreate(BaseModel):
    subject_id: int
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    difficulty: Difficulty = Difficulty.BEGINNER
    prerequisite_ids: list[int] = []

    _val_diff = field_validator("difficulty", mode="before")(_norm_diff)


class ConceptUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    difficulty: Difficulty | None = None

    _val_diff = field_validator("difficulty", mode="before")(_norm_diff)


class ConceptOut(BaseModel):
    id: int
    subject_id: int
    name: str
    description: str | None = None
    difficulty: Difficulty
    is_ai_generated: bool
    is_approved: bool | None = None
    prerequisites: list[ConceptRef] = []
    dependents: list[ConceptRef] = []
    mastery: float | None = None
    ai_explanation: str | None = None
    learning_debt: dict | None = None


class PrerequisiteCreate(BaseModel):
    prerequisite_id: int


class GraphNode(BaseModel):
    id: int
    name: str
    description: str | None = None
    difficulty: Difficulty
    mastery: float | None = None


class GraphEdge(BaseModel):
    source: int  # prerequisite
    target: int  # concept that depends on it


class KnowledgeGraph(BaseModel):
    subject_id: int
    graph_approved: bool
    nodes: list[GraphNode]
    edges: list[GraphEdge]

