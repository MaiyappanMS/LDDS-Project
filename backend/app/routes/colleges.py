from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_teacher
from app.database.connection import get_db
from app.models.college import College
from app.models.user import User
from app.schemas.college import CollegeCreate, CollegeOut
from app.services import subject_service

router = APIRouter(prefix="/api/colleges", tags=["Colleges"])


@router.post("", response_model=CollegeOut, status_code=status.HTTP_201_CREATED,
             summary="Create a college (teacher). The teacher is attached to it if they have none.")
def create_college(data: CollegeCreate, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    return subject_service.create_college(db, teacher, data)


@router.get("", response_model=list[CollegeOut], summary="List colleges (public, used by the registration form)")
def list_colleges(db: Session = Depends(get_db)):
    return list(db.scalars(select(College).order_by(College.name)))


@router.get("/{college_id}", response_model=CollegeOut, summary="Get a college")
def get_college(college_id: int, db: Session = Depends(get_db)):
    return subject_service.get_college(db, college_id)
