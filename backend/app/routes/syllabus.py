from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import require_teacher
from app.core.exceptions import FileValidationError
from app.database.connection import get_db
from app.models.user import User
from app.schemas.syllabus import SyllabusAnalysisResult, SyllabusOut
from app.services import syllabus_service

router = APIRouter(prefix="/api/syllabus", tags=["Syllabus"])


@router.post("/upload", response_model=SyllabusAnalysisResult, status_code=status.HTTP_201_CREATED,
             summary="Teacher: upload a PDF/DOCX/TXT syllabus; text is extracted and analysed by the AI")
def upload_syllabus(subject_id: int = Form(...), file: UploadFile = File(...),
                    teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    # Read at most max+1 bytes so an oversized upload is rejected without loading it all.
    data = file.file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise FileValidationError(f"File is too large. Maximum allowed size is {settings.max_upload_size_mb} MB.")
    return syllabus_service.upload_and_analyze(db, teacher, subject_id, file.filename, data)


@router.post("/{syllabus_id}/analyze", response_model=SyllabusAnalysisResult,
             summary="Teacher: (re)run analysis. Uses the cached AI result unless force=true.")
def analyze_syllabus(syllabus_id: int, force: bool = False, teacher: User = Depends(require_teacher),
                     db: Session = Depends(get_db)):
    return syllabus_service.analyze(db, teacher, syllabus_id, force=force)


@router.get("/subject/{subject_id}", response_model=list[SyllabusOut], summary="Teacher: syllabi uploaded for a subject")
def list_syllabi(subject_id: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    return syllabus_service.list_syllabi(db, teacher, subject_id)


@router.get("/{syllabus_id}", response_model=SyllabusOut, summary="Teacher: get a syllabus by id")
def get_syllabus(syllabus_id: int, teacher: User = Depends(require_teacher), db: Session = Depends(get_db)):
    return syllabus_service.get_owned_syllabus(db, teacher, syllabus_id)

