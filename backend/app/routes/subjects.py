from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_student, require_teacher
from app.database.connection import get_db
from app.models.user import User
from app.schemas.concept import KnowledgeGraph
from app.schemas.subject import SubjectCreate, SubjectOut
from app.services import concept_service, subject_service

router = APIRouter(prefix="/api/subjects", tags=["Subjects"])


@router.post("", response_model=SubjectOut, status_code=status.HTTP_201_CREATED, summary="Create a subject (teacher)")
def create_subject(data: SubjectCreate, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    s = subject_service.create_subject(db, teacher, data)
    return subject_service.serialize_subject(db, s, teacher)


@router.get("", response_model=list[SubjectOut],
            summary="Teacher: subjects you manage. Student: subjects you are enrolled in.")
def list_subjects(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [subject_service.serialize_subject(db, s, user) for s in subject_service.list_subjects(db, user)]


@router.get("/available", response_model=list[SubjectOut],
            summary="Student: subjects in your college you can still enroll in")
def available_subjects(student: User = Depends(require_student), db: Session = Depends(get_db)):
    return [subject_service.serialize_subject(db, s, student) for s in subject_service.list_available_subjects(db, student)]


@router.get("/{subject_id}", response_model=SubjectOut, summary="Get a subject")
def get_subject(subject_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = subject_service.assert_can_view(db, user, subject_id)
    return subject_service.serialize_subject(db, s, user)


@router.post("/{subject_id}/enroll", response_model=SubjectOut, summary="Student: enroll in a subject")
def enroll(subject_id: int, student: User = Depends(require_student), db: Session = Depends(get_db)):
    s = subject_service.enroll_student(db, student, subject_id)
    return subject_service.serialize_subject(db, s, student)


@router.get("/{subject_id}/knowledge-graph", response_model=KnowledgeGraph,
            tags=["Concepts"], summary="Nodes and edges of the prerequisite graph (edge: source -> target)")
def knowledge_graph(subject_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject = subject_service.assert_can_view(db, user, subject_id)
    return concept_service.knowledge_graph(db, subject, user=user)


@router.post("/{subject_id}/approve-graph", response_model=SubjectOut, tags=["Concepts"],
             summary="Teacher: approve the reviewed concept graph so students can be assessed")
def approve_graph(subject_id: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    subject = subject_service.assert_teacher_owns(db, teacher, subject_id)
    s = concept_service.approve_graph(db, subject)
    return subject_service.serialize_subject(db, s, teacher)

