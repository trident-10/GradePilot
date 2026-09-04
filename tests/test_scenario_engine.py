import pytest

from models.course import Course
from core.scenario_engine import (
    simulate_grade_change,
    simulate_multiple_grade_changes,
)


def create_courses():

    return [
        Course(
            code="CENG101",
            name="Programming",
            gpa_credit=4,
            grade="DD",
            semester="Test"
        ),
        Course(
            code="MATH101",
            name="Mathematics",
            gpa_credit=4,
            grade="BB",
            semester="Test"
        ),
    ]


def test_single_grade_change():

    courses = create_courses()

    result = simulate_grade_change(
        courses=courses,
        course_code="CENG101",
        new_grade="BB"
    )

    assert result["old_grade"] == "DD"
    assert result["new_grade"] == "BB"

    assert result["current_gpa"] == pytest.approx(2.0)
    assert result["new_gpa"] == pytest.approx(3.0)
    assert result["difference"] == pytest.approx(1.0)


def test_multiple_grade_changes():

    courses = create_courses()

    result = simulate_multiple_grade_changes(
        courses=courses,
        changes={
            "CENG101": "AA",
            "MATH101": "AA",
        }
    )

    assert result["current_gpa"] == pytest.approx(2.0)
    assert result["new_gpa"] == pytest.approx(4.0)
    assert result["difference"] == pytest.approx(2.0)

    assert len(result["changes"]) == 2


def test_invalid_grade_raises_error():

    courses = create_courses()

    with pytest.raises(ValueError):
        simulate_grade_change(
            courses=courses,
            course_code="CENG101",
            new_grade="ZZ"
        )


def test_missing_course_raises_error():

    courses = create_courses()

    with pytest.raises(ValueError):
        simulate_grade_change(
            courses=courses,
            course_code="NOTFOUND",
            new_grade="AA"
        )


def test_original_courses_are_not_modified():

    courses = create_courses()

    simulate_grade_change(
        courses=courses,
        course_code="CENG101",
        new_grade="AA"
    )

    assert courses[0].grade == "DD"