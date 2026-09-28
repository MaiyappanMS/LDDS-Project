"""Fallback for quick demos: create all tables directly (without Alembic history).
Prefer Alembic migrations:  alembic revision --autogenerate -m "initial schema"  &&  alembic upgrade head
Run:  python -m scripts.create_tables
"""
import app.models  # noqa: F401
from app.database.base import Base
from app.database.connection import engine

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Tables created:", ", ".join(sorted(Base.metadata.tables)))
