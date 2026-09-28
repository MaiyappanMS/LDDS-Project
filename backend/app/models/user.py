from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, enum_column
from app.models.enums import UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(enum_column(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    college_id: Mapped[int | None] = mapped_column(ForeignKey("colleges.id", ondelete="SET NULL"), nullable=True)

    college: Mapped["College | None"] = relationship(back_populates="users")
    enrollments: Mapped[list["SubjectEnrollment"]] = relationship(
        back_populates="student", cascade="all, delete"
    )
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="student", cascade="all, delete")

    @property
    def college_name(self) -> str | None:
        return self.college.name if self.college else None

