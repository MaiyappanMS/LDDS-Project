from datetime import datetime

from pydantic import BaseModel

from app.models.enums import MasteryStatus


class MasteryOut(BaseModel):
    concept_id: int
    concept: str
    correct_answers: int
    total_questions: int
    mastery_percentage: float
    confidence: float
    status: MasteryStatus


class DebtExplanation(BaseModel):
    summary: str
    why_it_matters: str
    recommended_order: list[str]


class DebtItem(BaseModel):
    concept_id: int
    concept: str
    mastery: float
    severity: str
    is_root_cause: bool
    priority_score: float
    caused_by: list[str] = []
    affected_concepts: list[str] = []
    affected_concept_refs: list[dict] = []
    why_it_matters: str | None = None
    recommended_action: str | None = None
    explanation: DebtExplanation | None = None


class LearningPathStep(BaseModel):
    order: int
    concept_id: int
    concept: str
    mastery: float | None = None
    status: str | None = None
    reason: str
    unblocks: list[str] = []


class LearningDebtReport(BaseModel):
    subject_id: int
    overall_mastery: float | None = None
    assessed_concepts: int
    debts: list[DebtItem]


class LearningPathResponse(BaseModel):
    subject_id: int
    steps: list[LearningPathStep]


class AssessmentHistoryItem(BaseModel):
    id: int
    subject_id: int | None = None
    subject_name: str | None = None
    student_name: str | None = None
    status: str
    score: float | None
    total_questions: int
    correct_count: int
    started_at: datetime
    completed_at: datetime | None


class StudentDashboard(BaseModel):
    subject_id: int | None = None
    subject_name: str | None = None
    overall_mastery: float | None
    strong_concepts: list[MasteryOut]
    weak_concepts: list[MasteryOut]
    learning_debt_count: int
    high_severity_debt: list[DebtItem] = []
    learning_path: list[LearningPathStep] = []
    assessment_history: list[AssessmentHistoryItem] = []
    recent_assessments: list[AssessmentHistoryItem] = []
    progress: list[dict] = []


class WeakConceptStat(BaseModel):
    concept_id: int
    concept: str
    name: str | None = None
    average_mastery: float
    students_assessed: int
    students_weak: int


class TeacherDashboard(BaseModel):
    subject_id: int | None = None
    subject_name: str | None = None
    graph_approved: bool | None = None
    enrolled_students: int = 0
    students_assessed: int = 0
    total_students: int | None = None
    total_subjects: int | None = None
    average_mastery: float | None = None
    high_debt_students: int | None = None
    total_assessments: int | None = None
    weak_concepts: list[WeakConceptStat] = []
    concept_performance: list[WeakConceptStat] = []
    debt_distribution: dict | None = None
    student_performance: list[dict] = []
    recent_assessments: list[dict] = []
    assessment_stats: dict = {}
    learning_debt_stats: dict = {}

