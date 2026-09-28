import os

from app.core.exceptions import FileValidationError, UnsupportedFileTypeError

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def get_extension(filename: str | None) -> str:
    return os.path.splitext(filename or "")[1].lower()


def validate_upload(filename: str | None, data: bytes, max_bytes: int) -> str:
    """Validate type, size and emptiness. Returns the normalised extension (e.g. '.pdf')."""
    ext = get_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError("Unsupported file type. Please upload a PDF, DOCX or TXT file.")
    if not data:
        raise FileValidationError("The uploaded file is empty.")
    if len(data) > max_bytes:
        raise FileValidationError(f"File is too large. Maximum allowed size is {max_bytes // (1024 * 1024)} MB.")
    if ext == ".pdf" and not data.lstrip()[:5].startswith(b"%PDF"):
        raise FileValidationError("This file has a .pdf extension but is not a valid PDF.")
    if ext == ".docx" and not data.startswith(b"PK"):
        raise FileValidationError("This file has a .docx extension but is not a valid DOCX document.")
    return ext


def safe_filename(filename: str | None) -> str:
    return os.path.basename(filename or "syllabus")[:200]
