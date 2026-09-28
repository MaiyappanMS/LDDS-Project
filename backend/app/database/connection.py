from collections.abc import Generator
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_engine():
    url = settings.database_url
    if url.startswith('sqlite'):
        return create_engine(url, connect_args={'check_same_thread': False})
    eng = create_engine(url, pool_pre_ping=True, pool_recycle=300)
    if 'unused_test_db' not in url:
        try:
            with eng.connect() as conn:
                conn.execute(text('SELECT 1'))
        except Exception as exc:
            logger.warning('PostgreSQL unavailable (%s); falling back to local SQLite learning_debt.db', exc)
            return create_engine('sqlite:///./learning_debt.db', connect_args={'check_same_thread': False})
    return eng


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
