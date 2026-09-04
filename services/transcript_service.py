from models.parse_result import ParseResult
from input.pdf_input import safe_pdf
from parsers.transcript_parser import (
    extract_text_from_pdf,
    analyze_and_parse_transcript,
)


def process_transcript(
    source_path: str,
    credit_relative_position: int | None = None,
    gpa_weighting_field: str | None = None,
) -> ParseResult:
    with safe_pdf(source_path) as safe_path:
        text = extract_text_from_pdf(safe_path)

        result = analyze_and_parse_transcript(
            text=text,
            credit_relative_position=credit_relative_position,
            gpa_weighting_field=gpa_weighting_field,
        )

    return result
