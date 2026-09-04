from __future__ import annotations

import math
from dataclasses import dataclass

from core.grade_scale import GRADE_POINTS
from core.scenario_engine import simulate_multiple_grade_changes
from models.course import Course
from parsers.transcript_parser import keep_latest_attempts
from services.academic_summary_service import AcademicSummaryValidationError


class ManualScenarioValidationError(AcademicSummaryValidationError):
    """Raised when a manual grade scenario is invalid."""


@dataclass(frozen=True)
class ManualScenarioChange:
    code: str
    name: str
    from_grade: str
    to_grade: str


@dataclass(frozen=True)
class ManualScenario:
    current_gpa: float
    projected_gpa: float
    gpa_change: float
    changes: list[ManualScenarioChange]


def build_manual_scenario(
    courses: list[Course],
    raw_changes: list[dict],
) -> ManualScenario:
    """
    Apply user-selected improvements to active/latest attempts.

    ``keep_latest_attempts`` is deliberately called before the scenario
    engine so historical repeats can never be modified. The engine remains
    the source of truth for GPA calculation and grade replacement.
    """

    if not raw_changes:
        raise ManualScenarioValidationError(
            "At least one grade change is required."
        )

    for course in courses:
        if (
            not math.isfinite(course.gpa_credit)
            or course.gpa_credit <= 0
        ):
            raise ManualScenarioValidationError(
                "Every course must have a positive finite GPA weight."
            )

    active_courses = keep_latest_attempts(courses)
    active_by_code = {course.code: course for course in active_courses}
    normalized_changes: dict[str, str] = {}

    for index, item in enumerate(raw_changes, start=1):
        course_code = item.get("course_code")
        new_grade = item.get("new_grade")

        if not isinstance(course_code, str) or not course_code.strip():
            raise ManualScenarioValidationError(
                f"Change #{index} is missing a valid course code."
            )
        if not isinstance(new_grade, str) or new_grade not in GRADE_POINTS:
            raise ManualScenarioValidationError(
                f"Change #{index} has an invalid grade."
            )

        code = course_code.strip()
        if code in normalized_changes:
            raise ManualScenarioValidationError(
                f"Duplicate change for course: {code}."
            )

        course = active_by_code.get(code)
        if course is None:
            raise ManualScenarioValidationError(
                f"Active course not found: {code}."
            )

        if GRADE_POINTS[new_grade] <= GRADE_POINTS[course.grade]:
            raise ManualScenarioValidationError(
                f"New grade for {code} must be higher than the current grade."
            )

        normalized_changes[code] = new_grade

    try:
        engine_result = simulate_multiple_grade_changes(
            courses=active_courses,
            changes=normalized_changes,
        )
    except (KeyError, ValueError) as exc:
        raise ManualScenarioValidationError(
            "Manual scenario could not be calculated."
        ) from exc

    response_changes = [
        ManualScenarioChange(
            code=code,
            name=active_by_code[code].name,
            from_grade=active_by_code[code].grade,
            to_grade=new_grade,
        )
        for code, new_grade in normalized_changes.items()
    ]

    return ManualScenario(
        current_gpa=float(engine_result["current_gpa"]),
        projected_gpa=float(engine_result["new_gpa"]),
        gpa_change=float(engine_result["difference"]),
        changes=response_changes,
    )
