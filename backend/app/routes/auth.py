from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserOut
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED,
             summary="Register a teacher or student")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user = auth_service.register_user(db, data)
    return TokenResponse(access_token=auth_service.issue_token(user), user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse, summary="Login with email and password (JSON)")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, data.email, data.password)
    return TokenResponse(access_token=auth_service.issue_token(user), user=UserOut.model_validate(user))


@router.post("/token", response_model=TokenResponse, include_in_schema=True,
             summary="OAuth2 form login (used by the Swagger 'Authorize' button; username = email)")
def login_form(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, form.username, form.password)
    return TokenResponse(access_token=auth_service.issue_token(user), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut, summary="Current authenticated user")
def me(user: User = Depends(get_current_user)):
    return user
