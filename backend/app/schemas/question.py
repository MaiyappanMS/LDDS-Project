from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import Difficulty, QuestionType

_Q_DIFF_MAP = {
    "easy": "BEGINNER", "basic": "BEGINNER", "beginner": "BEGINNER",
    "medium": "INTERMEDIATE", "moderate": "INTERMEDIATE", "intermediate": "INTERMEDIATE",
    "hard": "ADVANCED", "difficult": "ADVANCED", "advanced": "ADVANCED",
}


class QuestionGenerateRequest(BaseModel):
    subject_id: int
    concept_id: int
    number_of_questions: int = Field(default=3, ge=1, le=20)
    difficulty: Difficulty | None = None  # defaults to the concept's difficulty

    @model_validator(mode="before")
    @classmethod
    def _map_frontend_fields(cls, data):
        if isinstance(data, dict):
            data = dict(data)
            if "number_of_questions" not in data and "num_questions" in data:
                data["number_of_questions"] = data["num_questions"]
        return data

    @field_validator("difficulty", mode="before")
    @classmethod
    def _norm_diff(cls, v):
        if isinstance(v, str):
            k = v.strip().lower()
            if k in ("", "mixed", "all", "any"):
                return None
            return _Q_DIFF_MAP.get(k, k.upper())
        return v


class QuestionOut(BaseModel):
    """Teacher view - includes the answer."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    concept_id: int
    concept_name: str | None = None
    question_text: str
    question_type: QuestionType
    options: list[str]
    correct_answer: str
    explanation: str | None = None
    difficulty: Difficulty
    is_ai_generated: bool
    created_at: datetime



class QuestionPublic(BaseModel):
    """Student view - never contains the correct answer."""

    id: int
    concept_id: int
    concept_name: str
    question_text: str
    question_type: QuestionType
    difficulty: Difficulty
    options: list[str]
