from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    semester: str | None = Field(default=None, max_length=50)


class EnrolledStudentOut(BaseModel):
    id: int
    name: str
    full_name: str
    email: str
    mastery: float | None = None


class SubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    college_id: int
    name: str
    description: str | None = None
    semester: str | None = None
    created_by: int
    graph_approved: bool
    created_at: datetime
    student_count: int = 0
    concept_count: int = 0
    students: list[EnrolledStudentOut] = []
    assessment_stats: dict | None = None
    overall_mastery: float | None = None

