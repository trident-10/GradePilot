from copy import deepcopy

from models.course import Course
from core.gpa_engine import calculate_gpa
from core.grade_scale import GRADE_POINTS


def simulate_grade_change(
    courses: list[Course],
    course_code: str,
    new_grade: str
) -> dict:

    if new_grade not in GRADE_POINTS:
        raise ValueError(f"Invalid grade: {new_grade}")

    current_gpa = calculate_gpa(courses)

    simulated_courses = deepcopy(courses)

    old_grade = None

    for course in simulated_courses:
        if course.code == course_code:
            old_grade = course.grade
            course.grade = new_grade
            break

    if old_grade is None:
        raise ValueError(f"Course not found: {course_code}")

    new_gpa = calculate_gpa(simulated_courses)

    return {
        "course_code": course_code,
        "old_grade": old_grade,
        "new_grade": new_grade,
        "current_gpa": current_gpa,
        "new_gpa": new_gpa,
        "difference": new_gpa - current_gpa,
    }


def simulate_multiple_grade_changes(
    courses: list[Course],
    changes: dict[str, str]
) -> dict:

    current_gpa = calculate_gpa(courses)

    simulated_courses = deepcopy(courses)

    applied_changes = []

    for course_code, new_grade in changes.items():

        if new_grade not in GRADE_POINTS:
            raise ValueError(
                f"Invalid grade for {course_code}: {new_grade}"
            )

        course_found = False

        for course in simulated_courses:

            if course.code == course_code:
                old_grade = course.grade
                course.grade = new_grade

                applied_changes.append(
                    {
                        "course_code": course_code,
                        "old_grade": old_grade,
                        "new_grade": new_grade,
                    }
                )

                course_found = True
                break

        if not course_found:
            raise ValueError(
                f"Course not found: {course_code}"
            )

    new_gpa = calculate_gpa(simulated_courses)

    return {
        "current_gpa": current_gpa,
        "new_gpa": new_gpa,
        "difference": new_gpa - current_gpa,
        "changes": applied_changes,
    }