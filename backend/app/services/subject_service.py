from statistics import mean

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, ConflictError, ForbiddenError, NotFoundError
from app.models.assessment import Assessment
from app.models.college import College
from app.models.concept import Concept
from app.models.enums import AssessmentStatus, UserRole
from app.models.mastery import ConceptMastery
from app.models.subject import Subject, SubjectEnrollment
from app.models.user import User
from app.schemas.college import CollegeCreate
from app.schemas.subject import EnrolledStudentOut, SubjectCreate, SubjectOut


# ---------------------------------------------------------------- colleges
def create_college(db: Session, teacher: User, data: CollegeCreate) -> College:
    name = data.name.strip()
    existing = db.scalar(select(College).where(College.name.ilike(name)))
    if existing:
        raise ConflictError("A college with this name already exists.")
    college = College(name=name)
    db.add(college)
    db.flush()
    if teacher.college_id is None:
        teacher.college_id = college.id
    db.commit()
    db.refresh(college)
    return college


def get_college(db: Session, college_id: int) -> College:
    college = db.get(College, college_id)
    if not college:
        raise NotFoundError("College not found.")
    return college


# ---------------------------------------------------------------- subjects
def get_subject(db: Session, subject_id: int) -> Subject:
    subject = db.get(Subject, subject_id)
    if not subject:
        raise NotFoundError("Subject not found.")
    return subject


def assert_teacher_owns(db: Session, user: User, subject_id: int) -> Subject:
    subject = get_subject(db, subject_id)
    if user.role != UserRole.TEACHER or subject.created_by != user.id:
        raise ForbiddenError("You do not have access to this subject.")
    return subject


def is_enrolled(db: Session, student_id: int, subject_id: int) -> bool:
    return db.scalar(
        select(SubjectEnrollment.id).where(
            SubjectEnrollment.student_id == student_id, SubjectEnrollment.subject_id == subject_id
        )
    ) is not None


def assert_student_enrolled(db: Session, user: User, subject_id: int) -> Subject:
    subject = get_subject(db, subject_id)
    if user.role != UserRole.STUDENT or not is_enrolled(db, user.id, subject_id):
        raise ForbiddenError("You are not enrolled in this subject.")
    return subject


def assert_can_view(db: Session, user: User, subject_id: int) -> Subject:
    """Owning teacher or enrolled student."""
    if user.role == UserRole.TEACHER:
        return assert_teacher_owns(db, user, subject_id)
    return assert_student_enrolled(db, user, subject_id)


def create_subject(db: Session, teacher: User, data: SubjectCreate) -> Subject:
    if teacher.college_id is None:
        college = db.scalar(select(College).order_by(College.id))
        if not college:
            college = College(name="Default College")
            db.add(college)
            db.flush()
        teacher.college_id = college.id
        db.flush()
    subject = Subject(
        college_id=teacher.college_id,
        name=data.name.strip(),
        description=data.description,
        semester=data.semester,
        created_by=teacher.id,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


def list_subjects(db: Session, user: User) -> list[Subject]:
    if user.role == UserRole.TEACHER:
        stmt = select(Subject).where(Subject.created_by == user.id)
    else:
        stmt = select(Subject).join(SubjectEnrollment).where(SubjectEnrollment.student_id == user.id)
    return list(db.scalars(stmt.order_by(Subject.id)))


def list_available_subjects(db: Session, student: User) -> list[Subject]:
    """Subjects in the student's college that they have not enrolled in yet."""
    if student.college_id is None:
        return []
    enrolled = select(SubjectEnrollment.subject_id).where(SubjectEnrollment.student_id == student.id)
    stmt = select(Subject).where(Subject.college_id == student.college_id, Subject.id.not_in(enrolled))
    return list(db.scalars(stmt.order_by(Subject.id)))


def enroll_student(db: Session, student: User, subject_id: int) -> Subject:
    subject = get_subject(db, subject_id)
    if student.college_id is None:
        student.college_id = subject.college_id
        db.flush()
    elif subject.college_id != student.college_id:
        raise ForbiddenError("This subject belongs to a different college.")
    if is_enrolled(db, student.id, subject_id):
        raise ConflictError("You are already enrolled in this subject.")
    db.add(SubjectEnrollment(subject_id=subject_id, student_id=student.id))
    db.commit()
    return subject


def serialize_subject(db: Session, subject: Subject, user: User | None = None) -> SubjectOut:
    enrolled_users = list(
        db.scalars(
            select(User)
            .join(SubjectEnrollment, SubjectEnrollment.student_id == User.id)
            .where(SubjectEnrollment.subject_id == subject.id)
            .order_by(User.full_name)
        )
    )
    concept_count = db.scalar(select(func.count()).select_from(Concept).where(Concept.subject_id == subject.id)) or 0

    mastery_rows = db.execute(
        select(ConceptMastery.student_id, ConceptMastery.mastery_percentage)
        .where(ConceptMastery.subject_id == subject.id)
    ).all()
    by_student: dict[int, list[float]] = {}
    for sid, pct in mastery_rows:
        by_student.setdefault(sid, []).append(pct)

    students_out = [
        EnrolledStudentOut(
            id=u.id,
            name=u.full_name,
            full_name=u.full_name,
            email=u.email,
            mastery=round(mean(by_student[u.id]), 1) if u.id in by_student else None,
        )
        for u in enrolled_users
    ]

    completed = list(
        db.scalars(
            select(Assessment).where(
                Assessment.subject_id == subject.id, Assessment.status == AssessmentStatus.COMPLETED
            )
        )
    )
    scores = [a.score for a in completed if a.score is not None]
    stats = (
        {
            "completed_assessments": len(completed),
            "average_score": f"{round(mean(scores), 1)}%" if scores else "–",
            "highest_score": f"{round(max(scores), 1)}%" if scores else "–",
            "lowest_score": f"{round(min(scores), 1)}%" if scores else "–",
        }
        if completed
        else {}
    )

    overall_mastery: float | None = None
    if user and user.role == UserRole.STUDENT:
        vals = by_student.get(user.id, [])
        overall_mastery = round(mean(vals), 1) if vals else None
    else:
        all_vals = [v for vals in by_student.values() for v in vals]
        overall_mastery = round(mean(all_vals), 1) if all_vals else None

    return SubjectOut(
        id=subject.id,
        college_id=subject.college_id,
        name=subject.name,
        description=subject.description,
        semester=subject.semester,
        created_by=subject.created_by,
        graph_approved=subject.graph_approved,
        created_at=subject.created_at,
        student_count=len(enrolled_users),
        concept_count=concept_count,
        students=students_out,
        assessment_stats=stats,
        overall_mastery=overall_mastery,
    )

