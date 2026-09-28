from sqlalchemy import Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, enum_column
from app.models.enums import MasteryStatus


class ConceptMastery(Base, TimestampMixin):
    __tablename__ = "concept_mastery"
    __table_args__ = (UniqueConstraint("student_id", "concept_id", name="uq_mastery_student_concept"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    correct_answers: Mapped[int] = mapped_column(Integer, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    mastery_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0..1, grows with number of questions
    status: Mapped[MasteryStatus] = mapped_column(enum_column(MasteryStatus), nullable=False)

    concept: Mapped["Concept"] = relationship()
