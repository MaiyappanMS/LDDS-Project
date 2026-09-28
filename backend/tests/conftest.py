import os

import pytest

# Environment must be set BEFORE any `app` module is imported.
TEST_DB = os.environ.get("TEST_DATABASE_URL")
os.environ.setdefault("JWT_SECRET_KEY", "pytest-only-secret-key-not-for-production-0123456789")
os.environ["DATABASE_URL"] = TEST_DB or "postgresql+psycopg://user:pass@localhost:5432/unused_test_db"
os.environ.setdefault("AI_API_KEY", "test-key")
os.environ.setdefault("AI_MODEL", "test-model")


@pytest.fixture(scope="session")
def client():
    """API tests need a DISPOSABLE PostgreSQL database (e.g. a separate Neon branch): set TEST_DATABASE_URL.
    All tables are dropped and recreated, so the URL must contain 'test'."""
    if not TEST_DB:
        pytest.skip("Set TEST_DATABASE_URL to a disposable PostgreSQL database to run the API tests.")
    if "test" not in TEST_DB.lower():
        pytest.exit("Refusing to run: TEST_DATABASE_URL must contain 'test' because tables are dropped.")
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    import app.models  # noqa: F401
    from app.database.base import Base
    from app.database.connection import engine
    from app.main import app

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(engine)
