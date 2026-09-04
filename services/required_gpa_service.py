from __future__ import annotations

import math
from dataclasses import dataclass

from core.required_gpa_engine import calculate_required_semester_gpa
from models.course import Course
from parsers.transcript_parser import keep_latest_attempts
from services.academic_summary_service import AcademicSummaryValidationError


class RequiredGpaValidationError(AcademicSummaryValidationError):
    """Raised when required-semester-GPA request data is invalid."""


@dataclass(frozen=True)
class RequiredSemesterGpa:
    current_gpa: float
    target_gpa: float
    future_gpa_weight: float
    required_semester_gpa: float
    reachable: bool
    already_reached: bool


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def build_required_semester_gpa(
    courses: list[Course],
    target_gpa: object,
    future_gpa_weight: object,
) -> RequiredSemesterGpa:
    """
    Current points/weights use latest transcript attempts.

    already_reached follows the engine: required future quality points <= 0,
    not merely current_gpa >= target_gpa.
    """

    if not _is_finite_number(target_gpa):
        raise RequiredGpaValidationError(
            "Target GPA must be between 0.00 and 4.00"
        )
    numeric_target = float(target_gpa)
    if not 0.0 <= numeric_target <= 4.0:
        raise RequiredGpaValidationError(
            "Target GPA must be between 0.00 and 4.00"
        )

    if not _is_finite_number(future_gpa_weight):
        raise RequiredGpaValidationError(
            "Future GPA weight must be greater than 0."
        )
    numeric_weight = float(future_gpa_weight)
    if numeric_weight <= 0:
        raise RequiredGpaValidationError(
            "Future GPA weight must be greater than 0."
        )

    active_courses = keep_latest_attempts(courses)
    engine_result = calculate_required_semester_gpa(
        courses=active_courses,
        future_credits=numeric_weight,
        target_cgpa=numeric_target,
    )

    return RequiredSemesterGpa(
        current_gpa=float(engine_result["current_cgpa"]),
        target_gpa=numeric_target,
        future_gpa_weight=numeric_weight,
        required_semester_gpa=float(engine_result["required_semester_gpa"]),
        reachable=bool(engine_result["reachable"]),
        already_reached=bool(engine_result["already_reached"]),
    )
