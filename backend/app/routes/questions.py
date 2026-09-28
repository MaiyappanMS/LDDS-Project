from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_teacher
from app.database.connection import get_db
from app.models.user import User
from app.schemas.question import QuestionGenerateRequest, QuestionOut
from app.services import question_service

router = APIRouter(prefix="/api/questions", tags=["Questions"])


@router.post("/generate", response_model=list[QuestionOut], status_code=status.HTTP_201_CREATED,
             summary="Teacher: generate and store AI questions for one concept")
def generate(req: QuestionGenerateRequest, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    return question_service.generate_questions(db, teacher, req)


@router.get("/concept/{concept_id}", response_model=list[QuestionOut],
            summary="Teacher: list stored questions (with answers) for a concept")
def list_questions(concept_id: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    return question_service.list_for_concept(db, teacher, concept_id)


@router.get("/subject/{subject_id}", response_model=list[QuestionOut],
            summary="Teacher: list all stored questions (with answers) for a subject")
def list_subject_questions(subject_id: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    return question_service.list_for_subject(db, teacher, subject_id)


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Teacher: delete a question")
def delete_question(question_id: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    question_service.delete_question(db, teacher, question_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

