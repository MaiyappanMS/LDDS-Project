from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_student, require_teacher
from app.database.connection import get_db
from app.models.user import User
from app.schemas.assessment import (
    AssessmentCreate, AssessmentOut, AssessmentResult, AssessmentSubmit, TeacherAssessmentRow,
)
from app.schemas.question import QuestionPublic
from app.services import assessment_service

router = APIRouter(prefix="/api/assessments", tags=["Assessments"])


@router.post("", response_model=AssessmentOut, status_code=status.HTTP_201_CREATED,
             summary="Student: start an assessment (returns your unfinished one if it exists)")
def create_assessment(data: AssessmentCreate, student: User = Depends(require_student), db: Session = Depends(get_db)):
    return assessment_service.create_assessment(db, student, data)


@router.get("/subject/{subject_id}/results", response_model=list[TeacherAssessmentRow],
            summary="Teacher: completed assessments of students in your subject")
def teacher_results(subject_id: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    return assessment_service.teacher_results(db, teacher, subject_id)


@router.get("/{assessment_id}", response_model=AssessmentOut, summary="Get an assessment (owner student or subject teacher)")
def get_assessment(assessment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = assessment_service.get_assessment(db, user, assessment_id)
    return assessment_service.serialize_assessment(db, a)



@router.get("/{assessment_id}/questions", response_model=list[QuestionPublic],
            summary="Student: questions of your assessment (correct answers are NOT included)")
def get_questions(assessment_id: int, student: User = Depends(require_student), db: Session = Depends(get_db)):
    return assessment_service.get_questions(db, student, assessment_id)


@router.post("/{assessment_id}/submit", response_model=AssessmentResult,
             summary="Student: submit answers; returns score, mastery and learning debt")
def submit(assessment_id: int, data: AssessmentSubmit, student: User = Depends(require_student),
           db: Session = Depends(get_db)):
    return assessment_service.submit_assessment(db, student, assessment_id, data)
