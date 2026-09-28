from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_student, require_teacher
from app.core.exceptions import NotFoundError
from app.database.connection import get_db
from app.models.user import User
from app.schemas.learning_debt import (
    LearningDebtReport, LearningPathResponse, MasteryOut, StudentDashboard, TeacherDashboard,
)
from app.services import learning_debt_service, mastery_service, subject_service

students_router = APIRouter(prefix="/api/students/me", tags=["Learning Debt"])
teachers_router = APIRouter(prefix="/api/teachers/me", tags=["Learning Debt"])


@students_router.get("/mastery/{subject_id}", response_model=list[MasteryOut], summary="Your concept mastery")
def my_mastery(subject_id: int, student: User = Depends(require_student), db: Session = Depends(get_db)):
    subject_service.assert_student_enrolled(db, student, subject_id)
    return mastery_service.get_mastery(db, student.id, subject_id)


@students_router.get("/learning-debt/{subject_id}", response_model=LearningDebtReport,
                     summary="Your learning debt (deterministic) with any cached AI explanations")
def my_learning_debt(subject_id: int, student: User = Depends(require_student), db: Session = Depends(get_db)):
    subject_service.assert_student_enrolled(db, student, subject_id)
    return learning_debt_service.report(db, student.id, subject_id)


@students_router.post("/learning-debt/{subject_id}/explain", response_model=LearningDebtReport,
                      summary="Generate AI explanations for your most urgent debts (cached; scores are never changed)")
def explain_my_learning_debt(subject_id: int, student: User = Depends(require_student), db: Session = Depends(get_db)):
    subject_service.assert_student_enrolled(db, student, subject_id)
    return learning_debt_service.explain(db, student.id, subject_id)


@students_router.get("/learning-path/{subject_id}", response_model=LearningPathResponse,
                     summary="Personalised learning path from graph logic + mastery")
def my_learning_path(subject_id: int, student: User = Depends(require_student), db: Session = Depends(get_db)):
    subject_service.assert_student_enrolled(db, student, subject_id)
    return learning_debt_service.learning_path(db, student.id, subject_id)


@students_router.get("/dashboard", response_model=StudentDashboard, summary="Student overview dashboard across enrolled subjects")
def student_overview(student: User = Depends(require_student), db: Session = Depends(get_db)):
    return learning_debt_service.student_overview_dashboard(db, student)


@students_router.get("/dashboard/{subject_id}", response_model=StudentDashboard, summary="Student dashboard for a subject")
def student_dashboard(subject_id: int, student: User = Depends(require_student), db: Session = Depends(get_db)):
    return learning_debt_service.student_dashboard(db, student, subject_id)


@teachers_router.get("/dashboard", response_model=TeacherDashboard, summary="Teacher overview dashboard across all subjects")
def teacher_overview(teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    return learning_debt_service.teacher_overview_dashboard(db, teacher)


@teachers_router.get("/dashboard/{subject_id}", response_model=TeacherDashboard, summary="Teacher dashboard for a subject")
def teacher_dashboard(subject_id: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    return learning_debt_service.teacher_dashboard(db, teacher, subject_id)


@teachers_router.get("/students/{student_id}/learning-debt/{subject_id}", response_model=LearningDebtReport,
                     summary="Teacher: learning debt of one enrolled student")
def student_learning_debt(student_id: int, subject_id: int, teacher: User = Depends(require_teacher),
                          db: Session = Depends(get_db)):
    subject_service.assert_teacher_owns(db, teacher, subject_id)
    if not subject_service.is_enrolled(db, student_id, subject_id):
        raise NotFoundError("This student is not enrolled in the subject.")
    return learning_debt_service.report(db, student_id, subject_id)

