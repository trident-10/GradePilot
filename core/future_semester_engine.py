from models.course import Course
from core.gpa_baseline import anchored_current
from core.gpa_engine import calculate_gpa
from core.grade_scale import GRADE_POINTS


def calculate_future_semester_gpa(
    future_courses: list[Course]
) -> float:

    if not future_courses:
        return 0.0

    return calculate_gpa(
        future_courses
    )


def calculate_projected_cgpa(
    current_courses: list[Course],
    future_courses: list[Course],
    official_cgpa: float | None = None,
) -> dict:

    _, current_points, current_credits = anchored_current(
        current_courses, official_cgpa
    )

    future_credits = sum(
        course.gpa_credit
        for course in future_courses
    )

    future_points = sum(
        course.gpa_credit * GRADE_POINTS[course.grade]
        for course in future_courses
    )

    total_credits = (
        current_credits
        + future_credits
    )

    total_points = (
        current_points
        + future_points
    )

    if total_credits == 0:
        projected_cgpa = 0.0
    else:
        projected_cgpa = (
            total_points
            / total_credits
        )

    semester_gpa = calculate_future_semester_gpa(
        future_courses
    )

    return {
        "current_credits": current_credits,
        "future_credits": future_credits,
        "total_credits": total_credits,

        "current_points": current_points,
        "future_points": future_points,
        "total_points": total_points,

        "semester_gpa": semester_gpa,
        "projected_cgpa": projected_cgpa,
    }