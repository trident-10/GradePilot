import pytest

from models.course import Course
from core.target_engine import (
    analyze_target_gpa,
    find_target_plan,
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
            grade="CC",
            semester="Test"
        ),
    ]


def test_analyze_target_gpa():

    courses = create_courses()

    result = analyze_target_gpa(
        courses=courses,
        target_gpa=2.0
    )

    assert result["current_gpa"] == pytest.approx(1.5)

    assert result["total_credits"] == pytest.approx(8.0)

    assert result["current_points"] == pytest.approx(12.0)

    assert result["target_points"] == pytest.approx(16.0)

    assert result["required_points"] == pytest.approx(4.0)

    assert result["already_reached"] is False


def test_reachable_target():

    courses = create_courses()

    result = find_target_plan(
        courses=courses,
        target_gpa=2.0,
        strategy="min_courses",
        max_grade="BB"
    )

    assert result["reachable"] is True

    assert result["projected_gpa"] >= 2.0

    assert len(result["plan"]) > 0


def test_unreachable_target():

    courses = create_courses()

    result = find_target_plan(
        courses=courses,
        target_gpa=4.0,
        strategy="min_courses",
        max_grade="CC"
    )

    assert result["reachable"] is False

    assert result["projected_gpa"] < 4.0


def test_invalid_target_gpa():

    courses = create_courses()

    with pytest.raises(ValueError):
        find_target_plan(
            courses=courses,
            target_gpa=5.0,
            strategy="min_courses",
            max_grade="AA"
        )


def test_invalid_strategy():

    courses = create_courses()

    with pytest.raises(ValueError):
        find_target_plan(
            courses=courses,
            target_gpa=2.0,
            strategy="random_strategy",
            max_grade="AA"
        )


def test_minimal_change_strategy():

    courses = create_courses()

    result = find_target_plan(
        courses=courses,
        target_gpa=2.0,
        strategy="minimal_change",
        max_grade="AA"
    )

    assert result["reachable"] is True
    assert result["projected_gpa"] >= 2.0
    assert len(result["plan"]) > 0