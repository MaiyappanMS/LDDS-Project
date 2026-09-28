from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError
from app.models.question import Question
from app.models.user import User
from app.schemas.question import QuestionGenerateRequest
from app.services import ai_service, concept_service, subject_service


def generate_questions(db: Session, teacher: User, req: QuestionGenerateRequest) -> list[Question]:
    subject = subject_service.assert_teacher_owns(db, teacher, req.subject_id)
    concept = concept_service.get_concept(db, req.concept_id)
    if concept.subject_id != subject.id:
        raise AppError("The concept does not belong to this subject.", error_code="invalid_concept")

    drafts = ai_service.generate_questions(
        subject_name=subject.name, concept_name=concept.name, concept_description=concept.description,
        difficulty=req.difficulty or concept.difficulty, count=req.number_of_questions,
        prerequisite_names=[l.prerequisite.name for l in concept.prerequisite_links],
    )
    saved = []
    for d in drafts:
        q = Question(
            subject_id=subject.id, concept_id=concept.id, question_text=d.question_text.strip(),
            question_type=d.question_type, options=d.options, correct_answer=d.correct_answer,
            explanation=d.explanation or None, difficulty=d.difficulty, is_ai_generated=True, created_by=teacher.id,
        )
        db.add(q)
        saved.append(q)
    db.commit()
    for q in saved:
        db.refresh(q)
    return saved


def list_for_concept(db: Session, teacher: User, concept_id: int) -> list[Question]:
    concept = concept_service.get_concept(db, concept_id)
    subject_service.assert_teacher_owns(db, teacher, concept.subject_id)
    return list(db.scalars(select(Question).where(Question.concept_id == concept_id).order_by(Question.id)))


def list_for_subject(db: Session, teacher: User, subject_id: int) -> list[Question]:
    subject_service.assert_teacher_owns(db, teacher, subject_id)
    return list(db.scalars(select(Question).where(Question.subject_id == subject_id).order_by(Question.concept_id, Question.id)))


def delete_question(db: Session, teacher: User, question_id: int) -> None:
    q = db.get(Question, question_id)
    if not q:
        raise NotFoundError("Question not found.")
    subject_service.assert_teacher_owns(db, teacher, q.subject_id)
    db.delete(q)
    db.commit()

