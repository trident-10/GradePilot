from models.course import Course
from core.grade_scale import GRADE_POINTS


def calculate_required_semester_gpa(
    courses: list[Course],
    future_credits: float,
    target_cgpa: float
) -> dict:

    if future_credits <= 0:
        raise ValueError(
            "Future credits must be greater than 0."
        )

    if not 0.0 <= target_cgpa <= 4.0:
        raise ValueError(
            "Target CGPA must be between 0.00 and 4.00."
        )

    current_credits = sum(
        course.gpa_credit
        for course in courses
    )

    current_points = sum(
        course.gpa_credit * GRADE_POINTS[course.grade]
        for course in courses
    )

    current_cgpa = (
        current_points / current_credits
        if current_credits > 0
        else 0.0
    )

    total_credits = (
        current_credits + future_credits
    )

    required_total_points = (
        target_cgpa * total_credits
    )

    required_future_points = (
        required_total_points - current_points
    )

    required_semester_gpa = (
        required_future_points / future_credits
    )

    if required_semester_gpa <= 0:
        already_reached = True
        reachable = True

    elif required_semester_gpa <= 4.0:
        already_reached = False
        reachable = True

    else:
        already_reached = False
        reachable = False

    return {
        "current_cgpa": current_cgpa,
        "current_credits": current_credits,
        "future_credits": future_credits,
        "target_cgpa": target_cgpa,
        "total_credits": total_credits,
        "required_future_points": max(
            0.0,
            required_future_points
        ),
        "required_semester_gpa": max(
            0.0,
            required_semester_gpa
        ),
        "already_reached": already_reached,
        "reachable": reachable,
    }