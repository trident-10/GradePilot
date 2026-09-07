from models.parse_result import ParseResult
from input.pdf_input import (
    PDF_ERROR_UNREADABLE,
    PdfValidationError,
    safe_pdf,
)
from parsers.pdf_extraction import extract_text_from_pdf
from services.transcript_workflow import analyze_and_parse_transcript


def process_transcript(
    source_path: str,
    credit_relative_position: int | None = None,
    gpa_weighting_field: str | None = None,
    semantic_field_positions: dict[str, int] | None = None,
) -> ParseResult:
    with safe_pdf(source_path) as safe_path:
        try:
            text = extract_text_from_pdf(safe_path)
        except Exception as exc:
            raise PdfValidationError(PDF_ERROR_UNREADABLE) from exc

        if not text.strip():
            raise PdfValidationError(PDF_ERROR_UNREADABLE)

        result = analyze_and_parse_transcript(
            text=text,
            credit_relative_position=credit_relative_position,
            gpa_weighting_field=gpa_weighting_field,
            semantic_field_positions=semantic_field_positions,
        )

    return result
