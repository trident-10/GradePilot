import pytest

from models.course import Course
from core.semester_engine import (
    group_courses_by_semester,
    calculate_semester_gpas,
)


def create_courses():

    return [
        Course(
            code="CENG101",
            name="Programming",
            gpa_credit=4,
            grade="AA",
            semester="2025-2026 Güz"
        ),
        Course(
            code="MATH101",
            name="Mathematics",
            gpa_credit=4,
            grade="BB",
            semester="2025-2026 Güz"
        ),
        Course(
            code="CENG102",
            name="Programming II",
            gpa_credit=4,
            grade="CC",
            semester="2025-2026 Bahar"
        ),
    ]


def test_group_courses_by_semester():

    courses = create_courses()

    semesters = group_courses_by_semester(
        courses
    )

    assert len(
        semesters["2025-2026 Güz"]
    ) == 2

    assert len(
        semesters["2025-2026 Bahar"]
    ) == 1


def test_calculate_semester_gpas():

    courses = create_courses()

    results = calculate_semester_gpas(
        courses
    )

    fall = next(
        result
        for result in results
        if result["semester"] == "2025-2026 Güz"
    )

    spring = next(
        result
        for result in results
        if result["semester"] == "2025-2026 Bahar"
    )

    assert fall["gpa"] == pytest.approx(3.5)
    assert fall["credits"] == pytest.approx(8.0)

    assert spring["gpa"] == pytest.approx(2.0)
    assert spring["credits"] == pytest.approx(4.0)


def test_group_skips_courses_without_semester():

    courses = [
        Course(
            code="CENG101",
            name="Programming",
            gpa_credit=4,
            grade="AA",
            semester=None,
        ),
        Course(
            code="MATH101",
            name="Mathematics",
            gpa_credit=4,
            grade="BB",
            semester="2025-2026 Güz",
        ),
    ]

    grouped = group_courses_by_semester(courses)
    results = calculate_semester_gpas(courses)

    assert None not in grouped
    assert "" not in grouped
    assert list(grouped.keys()) == ["2025-2026 Güz"]
    assert len(results) == 1
    assert results[0]["semester"] == "2025-2026 Güz"