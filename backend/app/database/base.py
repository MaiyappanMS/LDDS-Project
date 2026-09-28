from datetime import datetime
import enum

from sqlalchemy import DateTime, Enum, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


def enum_column(enum_cls: type[enum.Enum]) -> Enum:
    """Store enums as plain VARCHAR (easy to migrate, no PG enum types to alter)."""
    return Enum(
        enum_cls,
        native_enum=False,
        length=32,
        create_constraint=False,
        values_callable=lambda e: [m.value for m in e],
    )
