from contextlib import nullcontext
from pathlib import Path

import pytest

from input.pdf_input import PdfValidationError
from models.parse_result import ParseResult
from services.transcript_service import process_transcript


def test_process_transcript_uses_safe_pdf_and_parser(
    monkeypatch,
    tmp_path,
):
    import services.transcript_service as service

    source_pdf = tmp_path / "random_student_file_name.pdf"
    source_pdf.write_bytes(b"dummy")

    safe_pdf_path = tmp_path / "safe_temp.pdf"
    safe_pdf_path.write_bytes(b"dummy")

    class FakeSafePdf:
        def __enter__(self):
            return str(safe_pdf_path)

        def __exit__(self, exc_type, exc_value, traceback):
            pass

    monkeypatch.setattr(
        service,
        "safe_pdf",
        lambda source_path: FakeSafePdf(),
    )

    monkeypatch.setattr(
        service,
        "extract_text_from_pdf",
        lambda path: "FAKE TRANSCRIPT TEXT",
    )

    expected_result = ParseResult(
        courses=[],
        format_name="generic",
        confidence=0.0,
        requires_user_confirmation=True,
        requires_credit_selection=True,
        warnings=[],
        credit_options=None,
    )

    monkeypatch.setattr(
        service,
        "analyze_and_parse_transcript",
        lambda text, credit_relative_position=None, gpa_weighting_field=None,
        semantic_field_positions=None: (
            expected_result
        ),
    )

    result = process_transcript(
        str(source_pdf),
    )

    assert result is expected_result


def test_process_transcript_rejects_pdf_without_extractable_text(
    monkeypatch,
    tmp_path,
):
    import services.transcript_service as service

    source_pdf = tmp_path / "source.pdf"
    source_pdf.write_bytes(b"dummy")

    monkeypatch.setattr(
        service,
        "safe_pdf",
        lambda source_path: nullcontext(str(source_pdf)),
    )
    monkeypatch.setattr(service, "extract_text_from_pdf", lambda path: "  \n")

    with pytest.raises(PdfValidationError, match="PDF okunamadı"):
        process_transcript(str(source_pdf))
