from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from api.schemas import (
    CourseResponse,
    CreditOptionResponse,
    TranscriptAnalyzeResponse,
)
from api.upload_temp import UploadTooLargeError, save_upload_to_temp
from api.weighting import (
    InvalidWeightingFieldError,
    public_option_id,
    resolve_weighting_field,
)
from input.pdf_input import PdfValidationError
from models.parse_result import ParseResult
from services.transcript_service import process_transcript

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


def build_analyze_response(result: ParseResult) -> TranscriptAnalyzeResponse:
    if result.requires_credit_selection:
        return TranscriptAnalyzeResponse(
            status="credit_selection",
            format=result.format_name,
            confidence=result.confidence,
            credit_options=_credit_option_responses(result),
            courses=[],
            warnings=list(result.warnings),
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
        )

    return TranscriptAnalyzeResponse(
        status="ready",
        format=result.format_name,
        confidence=result.confidence,
        credit_options=[],
        courses=courses,
        warnings=list(result.warnings),
    )


def analyze_uploaded_transcript(
    *,
    temp_path: str,
    weighting_field: str | None,
) -> ParseResult:
    if weighting_field is None:
        return process_transcript(temp_path)

    preview = process_transcript(temp_path)

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
        400: {"description": "Invalid PDF or weighting field"},
        413: {"description": "Upload exceeds size limit"},
        422: {"description": "Malformed multipart request"},
    },
)
def analyze_transcript(
    file: UploadFile = File(...),
    weighting_field: str | None = Form(default=None),
) -> TranscriptAnalyzeResponse:
    try:
        with save_upload_to_temp(file.file) as temp_path:
            try:
                result = analyze_uploaded_transcript(
                    temp_path=temp_path,
                    weighting_field=weighting_field,
                )
            except InvalidWeightingFieldError as exc:
                raise HTTPException(
                    status_code=400,
                    detail=str(exc),
                ) from exc
            except PdfValidationError as exc:
                raise HTTPException(
                    status_code=400,
                    detail=str(exc),
                ) from exc
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
