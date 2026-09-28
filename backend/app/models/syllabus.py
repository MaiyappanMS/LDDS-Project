from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, enum_column
from app.models.enums import SyllabusStatus


class Syllabus(Base, TimestampMixin):
    __tablename__ = "syllabi"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[SyllabusStatus] = mapped_column(
        enum_column(SyllabusStatus), nullable=False, default=SyllabusStatus.UPLOADED
    )
    # Cached validated AI output, so the AI is never called twice for the same syllabus.
    analysis_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    subject: Mapped["Subject"] = relationship(back_populates="syllabi")
    concepts: Mapped[list["Concept"]] = relationship(back_populates="syllabus")
