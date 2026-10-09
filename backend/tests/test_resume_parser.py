
from io import BytesIO

import pytest
from docx import Document
from pypdf import PdfWriter

from services import resume_parser


def make_docx(text):
    document = Document()
    document.add_paragraph(text)

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def make_blank_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)

    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_extract_text_from_valid_docx():
    file_bytes = make_docx(
        "Alex Morgan\nExperienced finance assistant."
    )

    result = resume_parser.extract_resume_text(
        "resume.docx",
        file_bytes,
    )

    assert "Alex Morgan" in result
    assert "Experienced finance assistant." in result


def test_docx_extension_is_case_insensitive():
    file_bytes = make_docx("Resume content")

    result = resume_parser.extract_resume_text(
        "RESUME.DOCX",
        file_bytes,
    )

    assert result == "Resume content"


def test_missing_filename_is_rejected():
    with pytest.raises(ValueError, match="No file was provided"):
        resume_parser.extract_resume_text("", b"some content")


def test_empty_file_is_rejected():
    with pytest.raises(ValueError, match="uploaded file is empty"):
        resume_parser.extract_resume_text("resume.pdf", b"")


def test_unsupported_extension_is_rejected():
    with pytest.raises(ValueError, match="Only PDF and DOCX"):
        resume_parser.extract_resume_text(
            "resume.txt",
            b"Some text",
        )


def test_corrupted_pdf_is_rejected():
    with pytest.raises(Exception):
        resume_parser.extract_resume_text(
            "resume.pdf",
            b"This is not a valid PDF file",
        )


def test_pdf_without_extractable_text_is_rejected():
    file_bytes = make_blank_pdf()

    with pytest.raises(
        ValueError,
        match="Could not extract any text",
    ):
        resume_parser.extract_resume_text(
            "blank.pdf",
            file_bytes,
        )


def test_pdf_extraction_is_called(monkeypatch):
    monkeypatch.setattr(
        resume_parser,
        "extract_text_from_pdf",
        lambda file_bytes: "Extracted resume text",
    )

    result = resume_parser.extract_resume_text(
        "resume.pdf",
        b"mock PDF bytes",
    )

    assert result == "Extracted resume text"


def test_docx_without_text_is_rejected():
    file_bytes = make_docx("")

    with pytest.raises(
        ValueError,
        match="Could not extract any text",
    ):
        resume_parser.extract_resume_text(
            "empty.docx",
            file_bytes,
        )


def test_corrupted_docx_is_rejected():
    with pytest.raises(Exception):
        resume_parser.extract_resume_text(
            "resume.docx",
            b"This is not a valid DOCX file",
        )