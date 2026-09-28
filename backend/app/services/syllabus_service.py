import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.models.enums import SyllabusStatus
from app.models.syllabus import Syllabus
from app.models.user import User
from app.schemas.syllabus import SyllabusAnalysisResult, SyllabusOut
from app.services import ai_service, concept_service, subject_service
from app.services.syllabus_parser import extract_text_from_file
from app.utils.validators import safe_filename

logger = logging.getLogger(__name__)


def upload_and_analyze(db: Session, teacher: User, subject_id: int, filename: str | None, data: bytes) -> SyllabusAnalysisResult:
    subject = subject_service.assert_teacher_owns(db, teacher, subject_id)
    if subject.graph_approved:
        raise ConflictError("This subject's concept graph is already approved. Concepts can still be edited manually.")
    text, file_type = extract_text_from_file(filename, data)  # raises controlled errors
    syllabus = Syllabus(
        subject_id=subject.id, uploaded_by=teacher.id, filename=safe_filename(filename), file_type=file_type,
        extracted_text=text, char_count=len(text), status=SyllabusStatus.UPLOADED,
    )
    db.add(syllabus)
    db.commit()
    db.refresh(syllabus)
    return analyze(db, teacher, syllabus.id, force=True)


def get_owned_syllabus(db: Session, teacher: User, syllabus_id: int) -> Syllabus:
    syllabus = db.get(Syllabus, syllabus_id)
    if not syllabus:
        raise NotFoundError("Syllabus not found.")
    subject_service.assert_teacher_owns(db, teacher, syllabus.subject_id)
    return syllabus


def analyze(db: Session, teacher: User, syllabus_id: int, force: bool = False) -> SyllabusAnalysisResult:
    """Run (or reuse the cached) AI analysis and store concepts + proposed prerequisites for teacher review."""
    syllabus = get_owned_syllabus(db, teacher, syllabus_id)
    subject = subject_service.get_subject(db, syllabus.subject_id)

    cached = syllabus.analysis_json is not None and not force
    if cached:
        analysis_dict = syllabus.analysis_json
    else:
        try:
            analysis = ai_service.analyze_syllabus(subject.name, syllabus.extracted_text)
        except AppError as exc:
            syllabus.status = SyllabusStatus.FAILED
            syllabus.error_message = exc.message
            db.commit()
            raise
        analysis_dict = analysis.model_dump(mode="json")
        syllabus.analysis_json = analysis_dict

    created, edges, warnings = concept_service.save_analysis(db, subject, syllabus.id, analysis_dict["concepts"])
    syllabus.status = SyllabusStatus.ANALYZED
    syllabus.error_message = None
    db.commit()
    db.refresh(syllabus)
    return SyllabusAnalysisResult(
        id=syllabus.id, status=syllabus.status, extracted_text=syllabus.extracted_text,
        syllabus=SyllabusOut.model_validate(syllabus), concepts_created=created,
        dependencies_created=edges, warnings=warnings, used_cached_analysis=cached,
    )



def list_syllabi(db: Session, teacher: User, subject_id: int) -> list[Syllabus]:
    subject_service.assert_teacher_owns(db, teacher, subject_id)
    return list(db.scalars(select(Syllabus).where(Syllabus.subject_id == subject_id).order_by(Syllabus.id.desc())))
