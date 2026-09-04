import pytest

from models.course import Course
from core.gpa_engine import calculate_gpa


def test_calculate_gpa():

    courses = [
        Course(
            code="TEST101",
            name="Test Course 1",
            gpa_credit=3,
            grade="AA",
            semester="Test"
        ),
        Course(
            code="TEST102",
            name="Test Course 2",
            gpa_credit=4,
            grade="BB",
            semester="Test"
        ),
        Course(
            code="TEST103",
            name="Test Course 3",
            gpa_credit=3,
            grade="BA",
            semester="Test"
        ),
    ]

    result = calculate_gpa(courses)

    assert result == pytest.approx(3.45)


def test_empty_course_list_returns_zero():

    result = calculate_gpa([])

    assert result == 0.0