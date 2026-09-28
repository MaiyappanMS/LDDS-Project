import io

import pytest

from app.core.exceptions import FileValidationError, UnsupportedFileTypeError
from app.services.syllabus_parser import extract_text_from_file

LONG = "Unit 1: Variables and data types. Unit 2: Loops and functions. " * 3


def test_txt_extraction():
    text, ext = extract_text_from_file("syllabus.txt", LONG.encode())
    assert ext == "txt" and "Variables" in text


def test_docx_extraction():
    docx = pytest.importorskip("docx")
    d = docx.Document()
    d.add_paragraph(LONG)
    buf = io.BytesIO()
    d.save(buf)
    text, ext = extract_text_from_file("syllabus.docx", buf.getvalue())
    assert ext == "docx" and "Loops" in text


def test_pdf_extraction_and_scanned_pdf_error():
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), LONG[:120])
    text, ext = extract_text_from_file("s.pdf", doc.tobytes())
    assert ext == "pdf" and "Variables" in text
    blank = fitz.open()
    blank.new_page()
    with pytest.raises(FileValidationError, match="OCR"):
        extract_text_from_file("scan.pdf", blank.tobytes())


@pytest.mark.parametrize("name,data,exc", [
    ("a.exe", b"x", UnsupportedFileTypeError),
    ("a.txt", b"", FileValidationError),
    ("a.pdf", b"not a pdf", FileValidationError),
    ("a.docx", b"PK-corrupt", FileValidationError),
    ("a.txt", b"too short", FileValidationError),
])
def test_invalid_files_are_rejected(name, data, exc):
    with pytest.raises(exc):
        extract_text_from_file(name, data)
