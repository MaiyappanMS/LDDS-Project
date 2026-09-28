import random
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError, ConflictError, ForbiddenError, NotFoundError
from app.models.answer import StudentAnswer
from app.models.assessment import Assessment, AssessmentQuestion
from app.models.concept import Concept
from app.models.enums import AssessmentStatus, QuestionType, UserRole
from app.models.question import Question
from app.models.user import User
from app.schemas.assessment import AnswerResult, AssessmentCreate, AssessmentOut, AssessmentResult, AssessmentSubmit, TeacherAssessmentRow
from app.schemas.question import QuestionPublic
from app.services import concept_service, learning_debt_service, mastery_service, subject_service


def create_assessment(db: Session, student: User, data: AssessmentCreate) -> Assessment:
    """Pick N stored questions per approved concept. Re-uses an unfinished assessment if one exists."""
    subject = subject_service.assert_student_enrolled(db, student, data.subject_id)
    if not subject.graph_approved:
        raise ConflictError("The teacher has not approved this subject's concept graph yet.")
    open_one = db.scalar(select(Assessment).where(
        Assessment.student_id == student.id, Assessment.subject_id == subject.id,
        Assessment.status == AssessmentStatus.IN_PROGRESS).order_by(Assessment.id.desc()))
    if open_one:
        return open_one

    per_concept = data.questions_per_concept or settings.default_questions_per_concept
    chosen: list[Question] = []
    for concept in concept_service.list_concepts(db, subject.id):
        pool = list(db.scalars(select(Question).where(Question.concept_id == concept.id)))
        chosen.extend(random.sample(pool, min(per_concept, len(pool))))
    if not chosen:
        raise AppError("This subject has no questions yet. Ask your teacher to generate questions.",
                       error_code="no_questions")
    assessment = Assessment(student_id=student.id, subject_id=subject.id, total_questions=len(chosen))
    db.add(assessment)
    db.flush()
    for pos, q in enumerate(chosen, start=1):
        db.add(AssessmentQuestion(assessment_id=assessment.id, question_id=q.id, position=pos))
    db.commit()
    db.refresh(assessment)
    return assessment


def get_assessment(db: Session, user: User, assessment_id: int) -> Assessment:
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise NotFoundError("Assessment not found.")
    if user.role == UserRole.STUDENT:
        if assessment.student_id != user.id:
            raise ForbiddenError("You can only access your own assessments.")
    else:
        subject_service.assert_teacher_owns(db, user, assessment.subject_id)
    return assessment


def _public_options(assessment_id: int, q: Question) -> list[str]:
    options = list(q.options)
    if q.question_type != QuestionType.TRUE_FALSE:  # stable per-assessment shuffle so the answer position varies
        random.Random(f"{assessment_id}-{q.id}").shuffle(options)
    return options


def get_questions(db: Session, student: User, assessment_id: int) -> list[QuestionPublic]:
    assessment = get_assessment(db, student, assessment_id)
    rows = db.execute(
        select(AssessmentQuestion, Question, Concept.name)
        .join(Question, Question.id == AssessmentQuestion.question_id)
        .join(Concept, Concept.id == Question.concept_id)
        .where(AssessmentQuestion.assessment_id == assessment.id).order_by(AssessmentQuestion.position))
    return [
        QuestionPublic(id=q.id, concept_id=q.concept_id, concept_name=cname, question_text=q.question_text,
                       question_type=q.question_type, difficulty=q.difficulty,
                       options=_public_options(assessment.id, q))
        for _, q, cname in rows
    ]


def serialize_assessment(db: Session, assessment: Assessment) -> AssessmentOut:
    from statistics import mean

    mastery_list = mastery_service.get_mastery(db, assessment.student_id, assessment.subject_id)
    overall = round(mean(m.mastery_percentage for m in mastery_list), 1) if mastery_list else None
    return AssessmentOut(
        id=assessment.id,
        student_id=assessment.student_id,
        subject_id=assessment.subject_id,
        status=assessment.status,
        started_at=assessment.started_at,
        completed_at=assessment.completed_at,
        score=assessment.score,
        total_questions=assessment.total_questions,
        correct_count=assessment.correct_count,
        overall_mastery=overall,
        concept_scores=mastery_list,
    )


def submit_assessment(db: Session, student: User, assessment_id: int, data: AssessmentSubmit) -> AssessmentResult:
    assessment = get_assessment(db, student, assessment_id)
    if assessment.status == AssessmentStatus.COMPLETED:
        raise ConflictError("This assessment has already been submitted.", error_code="already_submitted")

    questions = {
        q.id: (q, cname) for q, cname in db.execute(
            select(Question, Concept.name).join(Concept, Concept.id == Question.concept_id)
            .join(AssessmentQuestion, AssessmentQuestion.question_id == Question.id)
            .where(AssessmentQuestion.assessment_id == assessment.id))
    }
    submitted_ids = [a.question_id for a in data.answers]
    if len(set(submitted_ids)) != len(submitted_ids):
        raise AppError("Each question may be answered only once.", error_code="invalid_submission")
    unknown = set(submitted_ids) - set(questions)
    if unknown:
        raise AppError(f"Question(s) {sorted(unknown)} do not belong to this assessment.", error_code="invalid_submission")
    missing = set(questions) - set(submitted_ids)
    if missing:
        raise AppError(f"Please answer every question. Missing: {sorted(missing)}.", error_code="invalid_submission")

    now = datetime.now(timezone.utc)
    results, correct_total = [], 0
    for a in data.answers:
        q, cname = questions[a.question_id]
        selected = a.selected_answer.strip()
        stripped_opts = [o.strip() for o in q.options]
        if selected not in stripped_opts:
            pub_opts = _public_options(assessment.id, q)
            if len(selected) == 1 and "A" <= selected.upper() <= "Z":
                idx = ord(selected.upper()) - 65
                if 0 <= idx < len(pub_opts):
                    selected = pub_opts[idx].strip()
        if selected not in stripped_opts:
            raise AppError(f"Answer for question {q.id} is not one of its options.", error_code="invalid_submission")
        is_correct = selected == q.correct_answer.strip()
        correct_total += int(is_correct)
        db.add(StudentAnswer(assessment_id=assessment.id, question_id=q.id, student_id=student.id,
                             concept_id=q.concept_id, selected_answer=selected, is_correct=is_correct,
                             answered_at=now))
        results.append(AnswerResult(question_id=q.id, concept_id=q.concept_id, concept=cname,
                                    question_text=q.question_text, selected_answer=selected,
                                    correct_answer=q.correct_answer, is_correct=is_correct,
                                    explanation=q.explanation))
    assessment.status = AssessmentStatus.COMPLETED
    assessment.completed_at = now
    assessment.correct_count = correct_total
    assessment.total_questions = len(questions)
    assessment.score = round(correct_total / len(questions) * 100, 1)
    db.flush()

    mastery_service.recompute_mastery(db, student.id, assessment.subject_id)
    learning_debt_service.recompute_debt(db, student.id, assessment.subject_id)
    db.commit()
    db.refresh(assessment)

    a_out = serialize_assessment(db, assessment)
    return AssessmentResult(
        id=a_out.id,
        subject_id=a_out.subject_id,
        status=a_out.status,
        score=a_out.score,
        overall_mastery=a_out.overall_mastery,
        total_questions=a_out.total_questions,
        correct_count=a_out.correct_count,
        concept_scores=a_out.concept_scores,
        assessment=a_out,
        answers=results,
        mastery=a_out.concept_scores,
        learning_debt=learning_debt_service.debt_items(db, student.id, assessment.subject_id),
    )



def teacher_results(db: Session, teacher: User, subject_id: int) -> list[TeacherAssessmentRow]:
    subject_service.assert_teacher_owns(db, teacher, subject_id)
    rows = db.execute(
        select(Assessment, User.full_name).join(User, User.id == Assessment.student_id)
        .where(Assessment.subject_id == subject_id, Assessment.status == AssessmentStatus.COMPLETED)
        .order_by(Assessment.completed_at.desc()))
    return [TeacherAssessmentRow(assessment_id=a.id, student_id=a.student_id, student_name=name, score=a.score,
                                 correct_count=a.correct_count, total_questions=a.total_questions,
                                 completed_at=a.completed_at) for a, name in rows]
