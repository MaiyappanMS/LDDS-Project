from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    semester: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Students can only be assessed once the teacher approved the concept graph.
    graph_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    college: Mapped["College"] = relationship(back_populates="subjects")
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])
    syllabi: Mapped[list["Syllabus"]] = relationship(back_populates="subject", cascade="all, delete")
    concepts: Mapped[list["Concept"]] = relationship(back_populates="subject", cascade="all, delete")
    enrollments: Mapped[list["SubjectEnrollment"]] = relationship(
        back_populates="subject", cascade="all, delete"
    )


class SubjectEnrollment(Base, TimestampMixin):
    __tablename__ = "subject_enrollments"
    __table_args__ = (UniqueConstraint("subject_id", "student_id", name="uq_enrollment_subject_student"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    subject: Mapped["Subject"] = relationship(back_populates="enrollments")
    student: Mapped["User"] = relationship(back_populates="enrollments")
