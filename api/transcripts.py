from __future__ import annotations
from dataclasses import asdict

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from api.schemas import (
    CourseResponse,
    CreditOptionResponse,
    MappingCandidateResponse,
    TranscriptAnalyzeResponse,
    OfficialTranscriptSummaryResponse,
    OfficialSemesterSummaryResponse,
    TranscriptSemesterResponse,
    TranscriptIngestionErrorResponse,
)
from api.upload_temp import UploadTooLargeError, save_upload_to_temp
from api.weighting import (
    InvalidWeightingFieldError,
    public_option_id,
    public_mapping_candidate_id,
    resolve_weighting_field,
    resolve_semantic_field_positions,
)
from input.pdf_input import PdfValidationError
from models.parse_result import ParseResult
from services.transcript_service import process_transcript
from services.transcript_errors import TranscriptStructureError
from validation.mapping_validation import MappingValidationError

router = APIRouter(prefix="/api/transcripts", tags=["transcripts"])


def _course_response(course, index: int) -> CourseResponse:
    source_order = course.source_order
    if source_order is None:
        source_order = index

    return CourseResponse(
        code=course.code,
        name=course.name,
        gpa_credit=course.gpa_credit,
        ects=course.ects,
        local_credit=course.local_credit,
        grade=course.grade,
        semester=course.semester,
        source_order=source_order,
    )


def _credit_option_responses(
    result: ParseResult,
) -> list[CreditOptionResponse]:
    options = result.credit_options or []
    responses: list[CreditOptionResponse] = []
    used: set[str] = set()

    for index, option in enumerate(options, start=1):
        option_id = public_option_id(option, index)
        if option_id in used:
            option_id = f"field_{index}"
        used.add(option_id)
        responses.append(
            CreditOptionResponse(
                id=option_id,
                label=option.label,
            )
        )

    return responses


def _mapping_candidate_responses(
    result: ParseResult,
) -> list[MappingCandidateResponse]:
    return [
        MappingCandidateResponse(
            id=public_mapping_candidate_id(index),
            label=candidate.label,
            sample_values=list(candidate.sample_values),
            confidence=candidate.confidence,
        )
        for index, candidate in enumerate(
            result.mapping_candidates or [],
            start=1,
        )
    ]


def build_analyze_response(result: ParseResult) -> TranscriptAnalyzeResponse:
    document_fields = {}
    if result.document is not None:
        document_fields = dict(
            official_summary=OfficialTranscriptSummaryResponse(**asdict(result.document.summary)),
            semesters=[TranscriptSemesterResponse(
                label=semester.label, year=semester.year, term=semester.term,
                course_source_orders=semester.course_source_orders,
                official_summary=OfficialSemesterSummaryResponse(**asdict(semester.summary)) if semester.summary else None,
            ) for semester in result.document.semesters],
        )
    if result.requires_manual_mapping:
        return TranscriptAnalyzeResponse(
            status="manual_mapping",
            format=result.format_name,
            confidence=result.confidence,
            credit_options=[],
            mapping_candidates=_mapping_candidate_responses(result),
            courses=[],
            warnings=list(result.warnings),
            **document_fields,
        )

    if result.requires_credit_selection:
        return TranscriptAnalyzeResponse(
            status="credit_selection",
            format=result.format_name,
            confidence=result.confidence,
            credit_options=_credit_option_responses(result),
            courses=[],
            warnings=list(result.warnings),
            **document_fields,
        )

    courses = [
        _course_response(course, index)
        for index, course in enumerate(result.courses)
    ]

    if not courses:
        raise HTTPException(
            status_code=400,
            detail="Transcript could not be interpreted.",
        )

    if result.requires_user_confirmation:
        return TranscriptAnalyzeResponse(
            status="confirmation",
            format=result.format_name,
            confidence=result.confidence,
            credit_options=[],
            courses=courses,
            warnings=list(result.warnings),
            **document_fields,
        )

    return TranscriptAnalyzeResponse(
        status="ready",
        format=result.format_name,
        confidence=result.confidence,
        credit_options=[],
        courses=courses,
        warnings=list(result.warnings),
        **document_fields,
    )


def analyze_uploaded_transcript(
    *,
    temp_path: str,
    weighting_field: str | None,
    local_credit_field: str | None = None,
    ects_field: str | None = None,
) -> ParseResult:
    preview = process_transcript(temp_path)

    mapping_requested = bool(
        (local_credit_field and local_credit_field.strip())
        or (ects_field and ects_field.strip())
    )

    if mapping_requested:
        if not preview.requires_manual_mapping:
            raise MappingValidationError("mapping_not_applicable")

        semantic_positions = resolve_semantic_field_positions(
            local_credit_field=local_credit_field,
            ects_field=ects_field,
            candidates=preview.mapping_candidates,
        )
        mapped_preview = process_transcript(
            temp_path,
            semantic_field_positions=semantic_positions,
        )

        if weighting_field is None:
            return mapped_preview

        internal_field = resolve_weighting_field(
            weighting_field,
            mapped_preview.credit_options,
        )
        return process_transcript(
            temp_path,
            gpa_weighting_field=internal_field,
            semantic_field_positions=semantic_positions,
        )

    if weighting_field is None:
        return preview

    if not preview.requires_credit_selection:
        raise InvalidWeightingFieldError(
            "Invalid weighting field for this transcript."
        )

    internal_field = resolve_weighting_field(
        weighting_field,
        preview.credit_options,
    )

    return process_transcript(
        temp_path,
        gpa_weighting_field=internal_field,
    )


@router.post(
    "/analyze",
    response_model=TranscriptAnalyzeResponse,
    responses={
        400: {"description": "Invalid PDF, transcript or mapping request", "model": TranscriptIngestionErrorResponse},
        413: {"description": "Upload exceeds size limit"},
        422: {"description": "Malformed multipart request"},
    },
)
def analyze_transcript(
    file: UploadFile = File(...),
    weighting_field: str | None = Form(default=None),
    local_credit_field: str | None = Form(default=None),
    ects_field: str | None = Form(default=None),
) -> TranscriptAnalyzeResponse:
    try:
        with save_upload_to_temp(file.file) as temp_path:
            try:
                result = analyze_uploaded_transcript(
                    temp_path=temp_path,
                    weighting_field=weighting_field,
                    local_credit_field=local_credit_field,
                    ects_field=ects_field,
                )
            except MappingValidationError as exc:
                return JSONResponse(status_code=400, content={
                    "detail": str(exc), "error_type": "invalid_mapping_request", "code": exc.code,
                })
            except PdfValidationError as exc:
                raise HTTPException(
                    status_code=400,
                    detail=str(exc),
                ) from exc
            except TranscriptStructureError as exc:
                return JSONResponse(status_code=400, content={
                    "detail": str(exc), "error_type": "invalid_transcript",
                    "code": exc.issue.code if exc.issue else "invalid_transcript",
                })
            except ValueError as exc:
                raise HTTPException(
                    status_code=400,
                    detail="Transcript could not be interpreted.",
                ) from exc

            return build_analyze_response(result)

    except UploadTooLargeError as exc:
        raise HTTPException(
            status_code=413,
            detail=str(exc),
        ) from exc
    finally:
        file.file.close()
