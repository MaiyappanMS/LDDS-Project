"""Concept mastery = correct / total over the student's latest N answers for each concept (N = MASTERY_WINDOW).
Transparent MVP scoring, not a scientifically validated model."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.answer import StudentAnswer
from app.models.concept import Concept
from app.models.mastery import ConceptMastery
from app.models.enums import MasteryStatus
from app.schemas.learning_debt import MasteryOut
from app.services.debt_engine import Thresholds, calculate_mastery


def get_thresholds() -> Thresholds:
    return Thresholds.from_settings(settings)


def recompute_mastery(db: Session, student_id: int, subject_id: int) -> list[ConceptMastery]:
    """Recalculate and upsert ConceptMastery rows. Does not commit."""
    t = get_thresholds()
    rows = db.execute(
        select(StudentAnswer.concept_id, StudentAnswer.is_correct)
        .join(Concept, Concept.id == StudentAnswer.concept_id)
        .where(StudentAnswer.student_id == student_id, Concept.subject_id == subject_id)
        .order_by(StudentAnswer.answered_at.desc(), StudentAnswer.id.desc())
    ).all()

    per_concept: dict[int, list[bool]] = {}
    for concept_id, is_correct in rows:
        bucket = per_concept.setdefault(concept_id, [])
        if len(bucket) < settings.mastery_window:
            bucket.append(is_correct)

    existing = {
        m.concept_id: m
        for m in db.scalars(select(ConceptMastery).where(
            ConceptMastery.student_id == student_id, ConceptMastery.subject_id == subject_id))
    }
    result = []
    for concept_id, results in per_concept.items():
        calc = calculate_mastery(sum(results), len(results), t)
        row = existing.get(concept_id)
        if row is None:
            row = ConceptMastery(student_id=student_id, subject_id=subject_id, concept_id=concept_id, **calc)
            db.add(row)
        else:
            for k, v in calc.items():
                setattr(row, k, v)
        row.status = MasteryStatus(calc["status"])
        result.append(row)
    db.flush()
    return result


def get_mastery(db: Session, student_id: int, subject_id: int) -> list[MasteryOut]:
    stmt = (
        select(ConceptMastery, Concept.name)
        .join(Concept, Concept.id == ConceptMastery.concept_id)
        .where(ConceptMastery.student_id == student_id, ConceptMastery.subject_id == subject_id)
        .order_by(Concept.position, Concept.id)
    )
    return [
        MasteryOut(concept_id=m.concept_id, concept=name, correct_answers=m.correct_answers,
                   total_questions=m.total_questions, mastery_percentage=m.mastery_percentage,
                   confidence=m.confidence, status=m.status)
        for m, name in db.execute(stmt)
    ]


def mastery_map(db: Session, student_id: int, subject_id: int) -> dict[int, float]:
    stmt = select(ConceptMastery.concept_id, ConceptMastery.mastery_percentage).where(
        ConceptMastery.student_id == student_id, ConceptMastery.subject_id == subject_id)
    return {cid: pct for cid, pct in db.execute(stmt)}
