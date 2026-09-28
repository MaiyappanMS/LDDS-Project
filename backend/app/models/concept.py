from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, enum_column
from app.models.enums import Difficulty


class Concept(Base, TimestampMixin):
    __tablename__ = "concepts"
    __table_args__ = (UniqueConstraint("subject_id", "name", name="uq_concept_subject_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    syllabus_id: Mapped[int | None] = mapped_column(ForeignKey("syllabi.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[Difficulty] = mapped_column(
        enum_column(Difficulty), nullable=False, default=Difficulty.BEGINNER
    )
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    subject: Mapped["Subject"] = relationship(back_populates="concepts")
    syllabus: Mapped["Syllabus | None"] = relationship(back_populates="concepts")
    questions: Mapped[list["Question"]] = relationship(back_populates="concept", cascade="all, delete")
    # Rows where THIS concept is the dependent one (its prerequisites).
    prerequisite_links: Mapped[list["ConceptDependency"]] = relationship(
        foreign_keys="ConceptDependency.concept_id", back_populates="concept", cascade="all, delete"
    )
    # Rows where THIS concept is the prerequisite (concepts that depend on it).
    dependent_links: Mapped[list["ConceptDependency"]] = relationship(
        foreign_keys="ConceptDependency.prerequisite_id", back_populates="prerequisite", cascade="all, delete"
    )


class ConceptDependency(Base, TimestampMixin):
    """Edge of the knowledge graph:  prerequisite  ->  concept."""

    __tablename__ = "concept_dependencies"
    __table_args__ = (
        UniqueConstraint("concept_id", "prerequisite_id", name="uq_dependency_pair"),
        CheckConstraint("concept_id <> prerequisite_id", name="ck_dependency_not_self"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    prerequisite_id: Mapped[int] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_ai_proposed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    concept: Mapped["Concept"] = relationship(foreign_keys=[concept_id], back_populates="prerequisite_links")
    prerequisite: Mapped["Concept"] = relationship(foreign_keys=[prerequisite_id], back_populates="dependent_links")
