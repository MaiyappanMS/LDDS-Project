from collections.abc import Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.database.connection import get_db
from app.models.enums import UserRole
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError, TypeError):
        raise UnauthorizedError("Invalid authentication token.")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("User no longer exists or is inactive.")
    return user


def require_role(role: UserRole) -> Callable[..., User]:
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise ForbiddenError(f"This action requires the {role.value} role.")
        return user

    return checker


require_teacher = require_role(UserRole.TEACHER)
require_student = require_role(UserRole.STUDENT)
