from pathlib import Path

import pytest

from input.pdf_input import (
    PdfValidationError,
    safe_pdf,
    validate_pdf_file,
)


def test_nonexistent_pdf_is_rejected(tmp_path):
    missing_file = tmp_path / "does_not_exist.pdf"

    with pytest.raises(PdfValidationError):
        validate_pdf_file(str(missing_file))


def test_fake_pdf_is_rejected(tmp_path):
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_text(
        "This is not actually a PDF.",
        encoding="utf-8",
    )

    with pytest.raises(PdfValidationError):
        validate_pdf_file(str(fake_pdf))


def test_empty_pdf_is_rejected(tmp_path):
    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.touch()

    with pytest.raises(PdfValidationError):
        validate_pdf_file(str(empty_pdf))


def test_safe_pdf_removes_temporary_file(monkeypatch, tmp_path):
    source_pdf = tmp_path / "student_transcript.pdf"
    source_pdf.write_bytes(b"%PDF-test-content")

    import input.pdf_input as pdf_input

    monkeypatch.setattr(
        pdf_input,
        "validate_pdf_file",
        lambda path: pdf_input.ValidatedPdf(
            path=str(source_pdf),
            page_count=1,
            size_bytes=source_pdf.stat().st_size,
        ),
    )

    temporary_path = None

    with safe_pdf(str(source_pdf)) as pdf_path:
        temporary_path = Path(pdf_path)

        assert temporary_path.exists()
        assert temporary_path != source_pdf
        assert temporary_path.name != source_pdf.name

    assert temporary_path is not None
    assert not temporary_path.exists()

    # The original uploaded file must not be deleted.
    assert source_pdf.exists()