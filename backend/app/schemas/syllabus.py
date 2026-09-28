from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import SyllabusStatus


class SyllabusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    filename: str
    file_type: str
    char_count: int
    extracted_text: str | None = None
    status: SyllabusStatus
    error_message: str | None = None
    created_at: datetime


class SyllabusAnalysisResult(BaseModel):
    id: int | None = None
    status: SyllabusStatus | None = None
    extracted_text: str | None = None
    syllabus: SyllabusOut
    concepts_created: int
    dependencies_created: int
    warnings: list[str] = []
    used_cached_analysis: bool = False

