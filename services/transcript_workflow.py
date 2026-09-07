"""Application policy: mapping, weighting and review transitions."""
from models.credit_fields import parse_relative_field_key, relative_field_key
from models.transcript_ingestion import IngestionDecision
from parsers.document_parser import extract_transcript
from parsers.gpa_weighting import apply_gpa_weighting
from services.transcript_errors import TranscriptStructureError
from validation.transcript_validation import validate_selected_field, validate_transcript
from validation.mapping_validation import MappingValidationError, validate_mapping


def _raise_errors(report):
    if report.errors:
        raise TranscriptStructureError(report.errors[0])


def run_transcript_workflow(
    text: str,
    credit_relative_position: int | None = None,
    gpa_weighting_field: str | None = None,
    semantic_field_positions: dict[str, int] | None = None,
) -> IngestionDecision:
    field = gpa_weighting_field
    if field is None and credit_relative_position is not None:
        field = relative_field_key(credit_relative_position)
    try:
        if field is not None and not isinstance(field, str):
            raise ValueError("Invalid field type")
        legacy_position = parse_relative_field_key(field) if field is not None else None
    except ValueError as exc:
        raise MappingValidationError("invalid_weighting_field") from exc
    mapping = semantic_field_positions
    if legacy_position is not None:
        mapping, field = {"local_credit": legacy_position}, "local_credit"

    extraction = extract_transcript(text)
    report = validate_transcript(extraction)
    _raise_errors(report)
    if mapping is not None:
        validate_mapping(mapping, {c.relative_position for c in extraction.analysis.credit_candidates})
        extraction = extract_transcript(text, mapping)
        for mapped_field in mapping:
            if validate_selected_field(extraction, mapped_field).errors:
                raise MappingValidationError("incomplete_mapping")
    needs_review = extraction.format_name != "cankaya" or bool(report.issues)
    common = dict(extraction=extraction, issues=report.issues, needs_review=needs_review)
    available = set(extraction.field_positions)
    if extraction.format_name == "cankaya":
        available = {field for field in ("local_credit", "ects")
                     if all(getattr(course, field) is not None for course in extraction.courses)}
    if not available:
        return IngestionDecision("mapping_required", **common)
    if field is None:
        return IngestionDecision("weighting_required", **common)
    if field not in available:
        raise MappingValidationError("invalid_weighting_field")
    selected_report = validate_selected_field(extraction, field)
    if mapping is not None and selected_report.errors:
        raise MappingValidationError("incomplete_mapping")
    _raise_errors(selected_report)
    return IngestionDecision("review_required" if needs_review else "complete",
                             courses=apply_gpa_weighting(extraction.courses, field), **common)


def analyze_and_parse_transcript(
    text: str,
    credit_relative_position: int | None = None,
    gpa_weighting_field: str | None = None,
    semantic_field_positions: dict[str, int] | None = None,
):
    """Compatibility application entry point consumed by the upload service."""
    from services.transcript_presentation import present_transcript
    return present_transcript(run_transcript_workflow(
        text, credit_relative_position, gpa_weighting_field, semantic_field_positions,
    ))
