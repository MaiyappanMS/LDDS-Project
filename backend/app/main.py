import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.exceptions import AppError
from app.routes import assessments, auth, colleges, concepts, learning_debt, questions, subjects, syllabus, users

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        import app.models  # noqa: F401
        from app.database.base import Base
        from app.database.connection import engine

        Base.metadata.create_all(engine)
    except Exception as exc:
        logger.warning("Startup table check skipped: %s", exc)
    yield


app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    version="1.0.0",
    description="Detects a student's learning debt: weak prerequisite concepts that hold back later topics. "
                "Teachers upload any syllabus; the AI proposes a concept graph; the teacher approves it; "
                "deterministic logic then computes mastery, learning debt and a personalised learning path.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,  # Allow cookies/auth headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


def _error(status_code: int, code: str, message: str, headers: dict | None = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}}, headers=headers)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return _error(exc.status_code, exc.error_code, exc.message, headers)


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("Database error on %s %s", request.method, request.url.path)
    return _error(500, "database_error", "A database error occurred. Please try again.")


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return _error(500, "internal_error", "An unexpected error occurred.")


for module in (auth, users, colleges, subjects, syllabus, concepts, questions, assessments):
    app.include_router(module.router)
app.include_router(learning_debt.students_router)
app.include_router(learning_debt.teachers_router)


@app.get("/health", tags=["Health"], summary="Liveness check")
def health():
    return {"status": "ok"}
@app.get("/")
def home():
    return {"message": "Learning Debt Detection System API is running"}
