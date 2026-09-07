from __future__ import annotations

import math
from dataclasses import dataclass

from core.future_semester_engine import calculate_projected_cgpa
from core.gpa_baseline import anchored_current
from core.grade_scale import GRADE_POINTS
from models.course import Course
from parsers.transcript_parser import keep_latest_attempts
from services.academic_summary_service import (
    AcademicSummaryValidationError,
    validate_official_cgpa,
)

MAX_FUTURE_NAME_LENGTH = 200
MAX_FUTURE_COURSES = 40


class FutureSemesterValidationError(AcademicSummaryValidationError):
    """Raised when future-semester request data is invalid."""


@dataclass(frozen=True)
class FutureSemesterProjection:
    current_gpa: float
    future_semester_gpa: float
    projected_cgpa: float
    current_gpa_weight: float
    future_gpa_weight: float
    projected_total_weight: float


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def validate_and_build_future_courses(
    raw_courses: list[dict],
) -> list[Course]:
    if not isinstance(raw_courses, list):
        raise FutureSemesterValidationError(
            "Future course list is required."
        )

    if len(raw_courses) == 0:
        raise FutureSemesterValidationError(
            "At least one future course is required."
        )

    if len(raw_courses) > MAX_FUTURE_COURSES:
        raise FutureSemesterValidationError(
            "Too many future courses were provided."
        )

    courses: list[Course] = []

    for index, item in enumerate(raw_courses, start=1):
        if not isinstance(item, dict):
            raise FutureSemesterValidationError(
                f"Future course #{index} is invalid."
            )

        name = item.get("name")
        code = item.get("code")
        grade = item.get("grade")
        gpa_credit = item.get("gpa_credit")

        if not isinstance(name, str) or not name.strip():
            raise FutureSemesterValidationError(
                f"Future course #{index} is missing a valid name."
            )

        if len(name.strip()) > MAX_FUTURE_NAME_LENGTH:
            raise FutureSemesterValidationError(
                f"Future course #{index} name is too long."
            )

        if code is not None and (
            not isinstance(code, str) or not code.strip()
        ):
            raise FutureSemesterValidationError(
                f"Future course #{index} has an invalid code."
            )

        if code is not None and len(code.strip()) > MAX_FUTURE_NAME_LENGTH:
            raise FutureSemesterValidationError(
                f"Future course #{index} code is too long."
            )

        if not isinstance(grade, str) or grade not in GRADE_POINTS:
            raise FutureSemesterValidationError(
                f"Future course #{index} has an unknown grade."
            )

        if not _is_finite_number(gpa_credit):
            raise FutureSemesterValidationError(
                f"Future course #{index} has an invalid GPA weight."
            )

        numeric_weight = float(gpa_credit)
        if numeric_weight <= 0:
            raise FutureSemesterValidationError(
                f"Future course #{index} must have a positive GPA weight."
            )

        resolved_code = (
            code.strip()
            if isinstance(code, str) and code.strip()
            else None
        )

        courses.append(
            Course(
                # Missing code stays None; never copy the display name into code.
                code=resolved_code or "",
                name=name.strip(),
                gpa_credit=numeric_weight,
                grade=grade,
                semester="Future",
            )
        )

    return courses


def build_future_semester_projection(
    current_courses: list[Course],
    future_courses: list[Course],
    official_cgpa: float | None = None,
) -> FutureSemesterProjection:
    """
    Current GPA uses latest transcript attempts, anchored to official CGPA
    when the transcript printed one.
    """

    official = validate_official_cgpa(official_cgpa)
    active_current = keep_latest_attempts(current_courses)
    current_gpa, _, _ = anchored_current(active_current, official)
    engine_result = calculate_projected_cgpa(
        current_courses=active_current,
        future_courses=future_courses,
        official_cgpa=official,
    )

    return FutureSemesterProjection(
        current_gpa=float(current_gpa),
        future_semester_gpa=float(engine_result["semester_gpa"]),
        projected_cgpa=float(engine_result["projected_cgpa"]),
        current_gpa_weight=float(engine_result["current_credits"]),
        future_gpa_weight=float(engine_result["future_credits"]),
        projected_total_weight=float(engine_result["total_credits"]),
    )
