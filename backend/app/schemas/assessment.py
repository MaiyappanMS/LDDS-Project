from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import AssessmentStatus
from app.schemas.learning_debt import DebtItem, MasteryOut
from app.schemas.question import QuestionPublic


class AssessmentCreate(BaseModel):
    subject_id: int
    questions_per_concept: int | None = Field(default=None, ge=1, le=10)


class AssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    subject_id: int
    status: AssessmentStatus
    started_at: datetime
    completed_at: datetime | None = None
    score: float | None = None
    total_questions: int
    correct_count: int
    overall_mastery: float | None = None
    concept_scores: list[MasteryOut] = []


class AssessmentWithQuestions(BaseModel):
    assessment: AssessmentOut
    questions: list[QuestionPublic]


class AnswerSubmission(BaseModel):
    question_id: int
    selected_answer: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def _map_selected_option(cls, data):
        if isinstance(data, dict):
            data = dict(data)
            if not data.get("selected_answer") and data.get("selected_option") is not None:
                data["selected_answer"] = str(data["selected_option"])
        return data


class AssessmentSubmit(BaseModel):
    answers: list[AnswerSubmission] = Field(min_length=1)


class AnswerResult(BaseModel):
    question_id: int
    concept_id: int
    concept: str
    question_text: str
    selected_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str | None = None


class AssessmentResult(BaseModel):
    id: int | None = None
    subject_id: int | None = None
    status: AssessmentStatus | None = None
    score: float | None = None
    overall_mastery: float | None = None
    total_questions: int | None = None
    correct_count: int | None = None
    concept_scores: list[MasteryOut] = []
    assessment: AssessmentOut
    answers: list[AnswerResult]
    mastery: list[MasteryOut]
    learning_debt: list[DebtItem]


class TeacherAssessmentRow(BaseModel):
    assessment_id: int
    student_id: int
    student_name: str
    score: float | None
    correct_count: int
    total_questions: int
    completed_at: datetime | None

