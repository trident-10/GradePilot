from __future__ import annotations

from dataclasses import dataclass

from core.course_impact_engine import analyze_course_impact
from core.gpa_baseline import anchored_current
from models.course import Course
from parsers.transcript_parser import keep_latest_attempts
from services.academic_summary_service import (
    AcademicSummaryValidationError,
    validate_official_cgpa,
)


class CourseImpactValidationError(AcademicSummaryValidationError):
    """Raised when course-impact request data is invalid."""


@dataclass(frozen=True)
class CourseImpactOption:
    grade: str
    projected_gpa: float
    gpa_gain: float


@dataclass(frozen=True)
class CourseImpactCourse:
    code: str
    name: str
    current_grade: str
    gpa_weight: float


@dataclass(frozen=True)
class CourseImpact:
    course: CourseImpactCourse
    current_gpa: float
    options: list[CourseImpactOption]


def build_course_impact(
    courses: list[Course],
    course_code: object,
    official_cgpa: float | None = None,
) -> CourseImpact:
    """
    Impact analysis uses latest attempts (source_order).
    analyze_course_impact remains the source of truth for upgrade options.
    """

    if not isinstance(course_code, str) or not course_code.strip():
        raise CourseImpactValidationError("A course code is required.")

    selected_code = course_code.strip()
    official = validate_official_cgpa(official_cgpa)
    active_courses = keep_latest_attempts(courses)

    try:
        engine_result = analyze_course_impact(
            courses=active_courses,
            course_code=selected_code,
            official_cgpa=official,
        )
    except ValueError as exc:
        message = str(exc)
        if message.startswith("Course not found"):
            raise CourseImpactValidationError("Course not found.") from exc
        raise CourseImpactValidationError(
            "Course impact could not be calculated."
        ) from exc

    current_gpa, _, _ = anchored_current(active_courses, official)
    options = [
        CourseImpactOption(
            grade=str(item["grade"]),
            projected_gpa=float(item["new_gpa"]),
            gpa_gain=float(item["difference"]),
        )
        for item in engine_result["scenarios"]
    ]

    return CourseImpact(
        course=CourseImpactCourse(
            code=str(engine_result["course_code"]),
            name=str(engine_result["course_name"]),
            current_grade=str(engine_result["current_grade"]),
            gpa_weight=float(engine_result["credit"]),
        ),
        current_gpa=float(current_gpa),
        options=options,
    )
