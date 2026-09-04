import pytest

from models.course import Course
from core.required_gpa_engine import (
    calculate_required_semester_gpa,
)


def create_courses():

    return [
        Course(
            code="CENG101",
            name="Programming",
            gpa_credit=4,
            grade="BB",
            semester="Test"
        )
    ]


def test_required_semester_gpa():

    courses = create_courses()

    result = calculate_required_semester_gpa(
        courses=courses,
        future_credits=4,
        target_cgpa=3.5
    )

    assert result["current_cgpa"] == pytest.approx(3.0)

    assert result["required_semester_gpa"] == pytest.approx(4.0)

    assert result["reachable"] is True

    assert result["already_reached"] is False


def test_unreachable_required_gpa():

    courses = create_courses()

    result = calculate_required_semester_gpa(
        courses=courses,
        future_credits=4,
        target_cgpa=3.75
    )

    assert result["required_semester_gpa"] == pytest.approx(4.5)

    assert result["reachable"] is False

    assert result["already_reached"] is False


def test_invalid_future_credits():

    courses = create_courses()

    with pytest.raises(ValueError):
        calculate_required_semester_gpa(
            courses=courses,
            future_credits=0,
            target_cgpa=3.5
        )


def test_invalid_target_cgpa():

    courses = create_courses()

    with pytest.raises(ValueError):
        calculate_required_semester_gpa(
            courses=courses,
            future_credits=4,
            target_cgpa=5.0
        )


def test_current_above_target_still_needs_positive_semester_gpa():

    courses = [
        Course(
            code="OLD101",
            name="Completed Block A",
            gpa_credit=72,
            grade="BB",
            semester="Past"
        ),
        Course(
            code="OLD102",
            name="Completed Block B",
            gpa_credit=18,
            grade="BA",
            semester="Past"
        ),
    ]

    result = calculate_required_semester_gpa(
        courses=courses,
        future_credits=30,
        target_cgpa=3.0
    )

    assert result["current_cgpa"] == pytest.approx(3.10)
    assert result["current_credits"] == pytest.approx(90.0)
    assert result["already_reached"] is False
    assert result["reachable"] is True
    assert result["required_semester_gpa"] == pytest.approx(2.7)
    assert result["required_semester_gpa"] > 0


def test_target_guaranteed_with_zero_semester_gpa():

    courses = [
        Course(
            code="AA101",
            name="High Grade Course",
            gpa_credit=4,
            grade="AA",
            semester="Past"
        )
    ]

    result = calculate_required_semester_gpa(
        courses=courses,
        future_credits=4,
        target_cgpa=1.0
    )

    assert result["current_cgpa"] == pytest.approx(4.0)
    assert result["already_reached"] is True
    assert result["reachable"] is True
    assert result["required_semester_gpa"] == pytest.approx(0.0)