import pytest

from models.course import Course
from core.future_semester_engine import (
    calculate_future_semester_gpa,
    calculate_projected_cgpa,
)


def test_future_semester_gpa():

    future_courses = [
        Course(
            code="NEW101",
            name="Future Course",
            gpa_credit=4,
            grade="AA",
            semester="Future"
        )
    ]

    result = calculate_future_semester_gpa(
        future_courses
    )

    assert result == pytest.approx(4.0)


def test_projected_cgpa():

    current_courses = [
        Course(
            code="OLD101",
            name="Current Course",
            gpa_credit=4,
            grade="BB",
            semester="Current"
        )
    ]

    future_courses = [
        Course(
            code="NEW101",
            name="Future Course",
            gpa_credit=4,
            grade="AA",
            semester="Future"
        )
    ]

    result = calculate_projected_cgpa(
        current_courses=current_courses,
        future_courses=future_courses
    )

    assert result["current_credits"] == pytest.approx(4.0)

    assert result["future_credits"] == pytest.approx(4.0)

    assert result["total_credits"] == pytest.approx(8.0)

    assert result["current_points"] == pytest.approx(12.0)

    assert result["future_points"] == pytest.approx(16.0)

    assert result["semester_gpa"] == pytest.approx(4.0)

    assert result["projected_cgpa"] == pytest.approx(3.5)


def test_empty_future_semester():

    result = calculate_future_semester_gpa([])

    assert result == 0.0