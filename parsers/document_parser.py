"""Extract transcript facts. No validation policy, weighting or UI decisions."""

from models.transcript_extraction import TranscriptExtraction
from parsers.detector import detect_transcript_format
from parsers.formats.cankaya_parser import extract_cankaya_courses
from parsers.formats.generic_parser import extract_generic_courses
from parsers.generic_analyzer import analyze_generic_transcript
from parsers.rows import normalize_text, read_rows
from parsers.official_summary import extract_official_document


def extract_transcript(
    text: str, semantic_field_positions: dict[str, int] | None = None,
) -> TranscriptExtraction:
    text = normalize_text(text)
    rows = read_rows(text)
    analysis = analyze_generic_transcript(text, rows=rows)
    detection = detect_transcript_format(text)
    def with_document(extraction):
        extraction.document = extract_official_document(text, rows, extraction.courses)
        extraction.document.format_name = extraction.format_name
        extraction.document.confidence = extraction.confidence
        return extraction
    if detection.format_name == "cankaya" and semantic_field_positions is None:
        courses = extract_cankaya_courses(text, rows=rows)
        if courses and len(courses) == analysis.course_row_count:
            return with_document(TranscriptExtraction(rows, courses, analysis, format_name="cankaya", confidence=detection.confidence))
    positions = dict(semantic_field_positions) if semantic_field_positions is not None else {
        candidate.semantic_field: candidate.relative_position
        for candidate in analysis.credit_candidates
        if candidate.semantic_field is not None and candidate.confidence in {"high", "medium"}
    }
    courses = extract_generic_courses(
        text,
        local_credit_relative_position=positions.get("local_credit"),
        ects_relative_position=positions.get("ects"),
        use_row_headers=semantic_field_positions is None,
        rows=rows,
    ) if positions else []
    return with_document(TranscriptExtraction(rows, courses, analysis, field_positions=positions))
