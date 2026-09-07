from models.course import Course
from core.grade_scale import GRADE_POINTS
from core.scenario_engine import simulate_grade_change


def analyze_course_impact(
    courses: list[Course],
    course_code: str,
    official_cgpa: float | None = None,
) -> dict:

    selected_course = None

    for course in courses:
        if course.code == course_code:
            selected_course = course
            break

    if selected_course is None:
        raise ValueError(
            f"Course not found: {course_code}"
        )

    current_grade_point = GRADE_POINTS[
        selected_course.grade
    ]

    scenarios = []

    for grade, grade_point in GRADE_POINTS.items():

        if grade_point <= current_grade_point:
            continue

        result = simulate_grade_change(
            courses=courses,
            course_code=course_code,
            new_grade=grade,
            official_cgpa=official_cgpa,
        )

        scenarios.append({
            "grade": grade,
            "new_gpa": result["new_gpa"],
            "difference": result["difference"],
        })

    scenarios.sort(
        key=lambda item: GRADE_POINTS[item["grade"]]
    )

    return {
        "course_code": selected_course.code,
        "course_name": selected_course.name,
        "credit": selected_course.gpa_credit,
        "current_grade": selected_course.grade,
        "scenarios": scenarios,
    }