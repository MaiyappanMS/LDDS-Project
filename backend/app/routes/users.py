from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_teacher
from app.database.connection import get_db
from app.models.subject import SubjectEnrollment
from app.models.user import User
from app.schemas.user import UserOut
from app.services import subject_service

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserOut, summary="Current user profile")
def read_me(user: User = Depends(get_current_user)):
    return user


@router.get("/students", response_model=list[UserOut],
            summary="Teacher: students enrolled in one of your subjects")
def list_students(subject_id: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    subject_service.assert_teacher_owns(db, teacher, subject_id)
    stmt = (
        select(User)
        .join(SubjectEnrollment, SubjectEnrollment.student_id == User.id)
        .where(SubjectEnrollment.subject_id == subject_id)
        .order_by(User.full_name)
    )
    return list(db.scalars(stmt))
