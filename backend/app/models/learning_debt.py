from sqlalchemy import Boolean, Float, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class LearningDebt(Base, TimestampMixin):
    """One row per weak concept per student. Recomputed after every submitted assessment."""

    __tablename__ = "learning_debts"
    __table_args__ = (UniqueConstraint("student_id", "concept_id", name="uq_debt_student_concept"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    mastery_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # high | moderate
    priority_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_root_cause: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    affected_concept_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Cached AI explanation + a fingerprint of the inputs it was generated for.
    explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    explanation_key: Mapped[str | None] = mapped_column(String(64), nullable=True)

    concept: Mapped["Concept"] = relationship()
