from dataclasses import dataclass
from pathlib import Path
import tempfile
from contextlib import contextmanager

import pdfplumber

MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 50
PDF_MAGIC = b"%PDF-"
PDF_COPY_CHUNK_SIZE = 64 * 1024

PDF_ERROR_NOT_PDF = "Yüklenen dosya geçerli bir PDF değil."
PDF_ERROR_EMPTY = "PDF dosyası boş görünüyor."
PDF_ERROR_TOO_LARGE = "PDF dosyası çok büyük. Maksimum 10 MB yüklenebilir."
PDF_ERROR_TOO_MANY_PAGES = "PDF en fazla 50 sayfa olabilir."
PDF_ERROR_UNREADABLE = "PDF okunamadı. Farklı bir dosya deneyin."


@dataclass
class ValidatedPdf:
    path: str
    page_count: int
    size_bytes: int


class PdfValidationError(ValueError):
    pass


def validate_pdf_file(source_path: str) -> ValidatedPdf:
    source = Path(source_path)

    if not source.exists() or not source.is_file():
        raise PdfValidationError(PDF_ERROR_UNREADABLE)

    size_bytes = source.stat().st_size

    if size_bytes <= 0:
        raise PdfValidationError(PDF_ERROR_EMPTY)

    if size_bytes > MAX_PDF_SIZE_BYTES:
        raise PdfValidationError(PDF_ERROR_TOO_LARGE)

    with source.open("rb") as file:
        signature = file.read(len(PDF_MAGIC))

    if signature != PDF_MAGIC:
        raise PdfValidationError(PDF_ERROR_NOT_PDF)

    try:
        with pdfplumber.open(source) as pdf:
            page_count = len(pdf.pages)

            if page_count == 0:
                raise PdfValidationError(PDF_ERROR_UNREADABLE)

            if page_count > MAX_PDF_PAGES:
                raise PdfValidationError(PDF_ERROR_TOO_MANY_PAGES)

    except PdfValidationError:
        raise

    except Exception as exc:
        raise PdfValidationError(PDF_ERROR_UNREADABLE) from exc

    return ValidatedPdf(
        path=str(source),
        page_count=page_count,
        size_bytes=size_bytes,
    )


def create_safe_temp_pdf(source_path: str) -> str:
    validated = validate_pdf_file(source_path)

    temp_file = tempfile.NamedTemporaryFile(
        prefix="gradepilot_pdf_",
        suffix=".pdf",
        delete=False,
    )
    temp_path = Path(temp_file.name)

    try:
        try:
            with open(validated.path, "rb") as source:
                while True:
                    chunk = source.read(PDF_COPY_CHUNK_SIZE)
                    if not chunk:
                        break
                    temp_file.write(chunk)
            temp_file.flush()
        finally:
            temp_file.close()
        return str(temp_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise

@contextmanager
def safe_pdf(source_path: str):
    temp_path = create_safe_temp_pdf(source_path)

    try:
        yield temp_path
    finally:
        temp_file = Path(temp_path)

        if temp_file.exists():
            temp_file.unlink()