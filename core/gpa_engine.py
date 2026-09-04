from models.course import Course
from core.grade_scale import GRADE_POINTS


def calculate_gpa(courses: list[Course]) -> float:
    total_points = 0
    total_credits = 0

    for course in courses:
        grade_point = GRADE_POINTS[course.grade]

        total_points += course.gpa_credit * grade_point
        total_credits += course.gpa_credit

    if total_credits == 0:
        return 0.0

    return total_points / total_credits