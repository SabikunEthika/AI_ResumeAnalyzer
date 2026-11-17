from io import BytesIO
from zipfile import BadZipFile, ZipFile

from docx import Document
from pypdf import PdfReader


def extract_text_from_pdf(file_bytes):
    reader = PdfReader(BytesIO(file_bytes))

    if reader.is_encrypted:
        raise ValueError("Password-protected PDFs are not supported.")

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text.strip()


def extract_text_from_docx(file_bytes):
    try:
        with ZipFile(BytesIO(file_bytes)) as archive:
            if "[Content_Types].xml" not in archive.namelist() or (
                "word/document.xml" not in archive.namelist()
            ):
                raise ValueError("The DOCX file is invalid or unsupported.")
    except BadZipFile as error:
        raise ValueError("The DOCX file is invalid or corrupted.") from error

    document = Document(BytesIO(file_bytes))

    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text.strip()


def extract_resume_text(filename, file_bytes):
    if not filename:
        raise ValueError("No file was provided.")

    if not file_bytes:
        raise ValueError("The uploaded file is empty.")

    filename = filename.lower()

    if filename.endswith(".pdf"):
        if not file_bytes.startswith(b"%PDF-"):
            raise ValueError("The uploaded PDF file is invalid or corrupted.")
        text = extract_text_from_pdf(file_bytes)

    elif filename.endswith(".docx"):
        if not file_bytes.startswith(b"PK"):
            raise ValueError("The uploaded DOCX file is invalid or corrupted.")
        text = extract_text_from_docx(file_bytes)

    else:
        raise ValueError("Only PDF and DOCX files are supported.")

    if not text:
        raise ValueError("Could not extract any text from the resume.")

    return text
