import pytest

from models.course import Course
from core.course_impact_engine import analyze_course_impact


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
            grade="AA",
            semester="Test"
        ),
    ]


def test_course_impact():

    courses = create_courses()

    result = analyze_course_impact(
        courses=courses,
        course_code="CENG101"
    )

    assert result["course_code"] == "CENG101"

    assert result["current_grade"] == "DD"

    assert result["credit"] == pytest.approx(4.0)

    grades = [
        scenario["grade"]
        for scenario in result["scenarios"]
    ]

    assert grades == [
        "DC",
        "CC",
        "CB",
        "BB",
        "BA",
        "AA",
    ]


def test_course_impact_aa_result():

    courses = create_courses()

    result = analyze_course_impact(
        courses=courses,
        course_code="CENG101"
    )

    aa_scenario = next(
        scenario
        for scenario in result["scenarios"]
        if scenario["grade"] == "AA"
    )

    assert aa_scenario["new_gpa"] == pytest.approx(4.0)

    assert aa_scenario["difference"] == pytest.approx(1.5)


def test_course_not_found():

    courses = create_courses()

    with pytest.raises(ValueError):
        analyze_course_impact(
            courses=courses,
            course_code="UNKNOWN"
        )


def test_course_already_aa():

    courses = create_courses()

    result = analyze_course_impact(
        courses=courses,
        course_code="MATH101"
    )

    assert result["current_grade"] == "AA"

    assert result["scenarios"] == []