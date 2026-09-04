from models.course import Course
from core.gpa_engine import calculate_gpa


def group_courses_by_semester(
    courses: list[Course]
) -> dict[str, list[Course]]:

    semesters = {}

    for course in courses:

        if course.semester is None:
            continue

        if course.semester not in semesters:
            semesters[course.semester] = []

        semesters[course.semester].append(course)

    return semesters


def calculate_semester_gpas(
    courses: list[Course]
) -> list[dict]:

    semesters = group_courses_by_semester(courses)

    results = []

    for semester, semester_courses in semesters.items():

        semester_gpa = calculate_gpa(
            semester_courses
        )

        total_credits = sum(
            course.gpa_credit
            for course in semester_courses
        )

        results.append({
            "semester": semester,
            "gpa": semester_gpa,
            "credits": total_credits,
            "course_count": len(semester_courses),
        })

    return results