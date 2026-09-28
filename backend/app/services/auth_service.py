from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.college import College
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import RegisterRequest


def _resolve_college(db: Session, data: RegisterRequest) -> College | None:
    if data.college_id is not None:
        college = db.get(College, data.college_id)
        if not college:
            raise NotFoundError("College not found.")
        return college
    if data.college_name and data.college_name.strip():
        name = data.college_name.strip()
        college = db.scalar(select(College).where(func.lower(College.name) == name.lower()))
        if college:
            return college
        college = College(name=name)
        db.add(college)
        db.flush()
        return college
    existing = db.scalar(select(College).order_by(College.id))
    if existing:
        return existing
    if data.role == UserRole.TEACHER:
        college = College(name="Default College")
        db.add(college)
        db.flush()
        return college
    return None



def register_user(db: Session, data: RegisterRequest) -> User:
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise ConflictError("An account with this email already exists.")
    college = _resolve_college(db, data)
    user = User(
        email=email,
        full_name=data.full_name.strip(),
        hashed_password=hash_password(data.password),
        role=data.role,
        college_id=college.id if college else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if not user or not verify_password(password, user.hashed_password) or not user.is_active:
        raise UnauthorizedError("Incorrect email or password.")
    return user


def issue_token(user: User) -> str:
    return create_access_token(user.id, user.role.value)
