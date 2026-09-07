"""Anchor cumulative GPA math to an explicitly printed transcript CGPA when present."""
from __future__ import annotations

from models.course import Course
from core.grade_scale import GRADE_POINTS


def course_quality_points(courses: list[Course]) -> tuple[float, float]:
    credits = sum(course.gpa_credit for course in courses)
    points = sum(
        course.gpa_credit * GRADE_POINTS[course.grade] for course in courses
    )
    return float(points), float(credits)


def anchored_current(
    courses: list[Course],
    official_cgpa: float | None = None,
) -> tuple[float, float, float]:
    """
    Returns (current_gpa, current_points, credits).

    When official_cgpa is set, quality points are official * credits so planners
    start from the printed transcript CGPA without rewriting course rows.
    """
    points, credits = course_quality_points(courses)
    if credits <= 0:
        return 0.0, 0.0, 0.0
    if official_cgpa is not None:
        return float(official_cgpa), float(official_cgpa) * credits, credits
    return points / credits, points, credits


def anchor_projected_gpa(
    derived_current: float,
    derived_projected: float,
    official_cgpa: float | None,
) -> tuple[float, float]:
    """Shift a course-derived projection so its baseline matches official CGPA."""
    if official_cgpa is None:
        return derived_current, derived_projected
    return float(official_cgpa), float(official_cgpa) + (
        derived_projected - derived_current
    )
