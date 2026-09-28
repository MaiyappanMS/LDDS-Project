from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class College(Base, TimestampMixin):
    __tablename__ = "colleges"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="college")
    subjects: Mapped[list["Subject"]] = relationship(back_populates="college", cascade="all, delete")
