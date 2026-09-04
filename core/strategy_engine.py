from models.course import Course
from core.scenario_engine import simulate_grade_change


def rank_grade_improvements(
    courses: list[Course],
    target_grade: str = "AA"
) -> list[dict]:

    results = []

    for course in courses:
        simulation = simulate_grade_change(
            courses,
            course.code,
            target_grade
        )

        results.append(simulation)

    results.sort(
        key=lambda item: item["difference"],
        reverse=True
    )

    return results