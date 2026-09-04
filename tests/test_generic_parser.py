import pytest

from parsers.formats.generic_parser import (
    parse_generic_courses,
)


SAMPLE_LINE = (
    "CENG111 Programming Z Tr 3 2 4 6 DD 1.00"
)


def test_first_numeric_credit_mode():

    courses = parse_generic_courses(
        SAMPLE_LINE,
        credit_mode="first_numeric",
    )

    assert len(courses) == 1
    assert courses[0].code == "CENG111"
    assert courses[0].grade == "DD"
    assert courses[0].gpa_credit == pytest.approx(3.0)
    assert courses[0].ects is None
    assert courses[0].source_order == 0
    assert courses[0].semester is None


def test_last_numeric_credit_mode():

    courses = parse_generic_courses(
        SAMPLE_LINE,
        credit_mode="last_numeric",
    )

    assert len(courses) == 1
    assert courses[0].gpa_credit == pytest.approx(1.0)


def test_missing_credit_mode_requires_selection():

    with pytest.raises(ValueError):
        parse_generic_courses(
            SAMPLE_LINE,
            credit_mode=None,
        )


def test_unsupported_credit_mode():

    with pytest.raises(ValueError):
        parse_generic_courses(
            SAMPLE_LINE,
            credit_mode="gpa_credit",
        )


def test_relative_position_cleans_name_and_ects():

    text = """
Course Credit ECTS Grade
CENG101 Programming 3 6 BA
CENG102 Data Structures 4 7 BB
"""

    courses = parse_generic_courses(
        text,
        credit_relative_position=-2,
        ects_relative_position=-1,
    )

    assert len(courses) == 2

    assert courses[0].code == "CENG101"
    assert courses[0].name == "Programming"
    assert courses[0].gpa_credit == pytest.approx(3.0)
    assert courses[0].ects == pytest.approx(6.0)
    assert courses[0].grade == "BA"

    assert courses[1].code == "CENG102"
    assert courses[1].name == "Data Structures"
    assert courses[1].gpa_credit == pytest.approx(4.0)
    assert courses[1].ects == pytest.approx(7.0)
    assert courses[1].grade == "BB"


def test_ects_is_not_guessed_without_position():

    courses = parse_generic_courses(
        "CENG101 Programming 3 6 BA",
        credit_relative_position=-2,
    )

    assert courses[0].name == "Programming"
    assert courses[0].gpa_credit == pytest.approx(3.0)
    assert courses[0].ects is None


def test_compact_course_code():

    courses = parse_generic_courses(
        "CENG101 Programming 3 6 BA",
        credit_relative_position=-2,
        ects_relative_position=-1,
    )

    assert len(courses) == 1
    assert courses[0].code == "CENG101"
    assert courses[0].name == "Programming"
    assert courses[0].gpa_credit == pytest.approx(3.0)
    assert courses[0].ects == pytest.approx(6.0)
    assert courses[0].grade == "BA"


def test_split_course_code():

    courses = parse_generic_courses(
        "CENG 101 Programming 3 6 BA",
        credit_relative_position=-2,
        ects_relative_position=-1,
    )

    assert len(courses) == 1
    assert courses[0].code == "CENG101"
    assert courses[0].name == "Programming"
    assert courses[0].gpa_credit == pytest.approx(3.0)
    assert courses[0].ects == pytest.approx(6.0)
    assert courses[0].grade == "BA"


def test_split_course_code_multiword_name():

    courses = parse_generic_courses(
        "CENG 102 Data Structures 4 7 BB",
        credit_relative_position=-2,
        ects_relative_position=-1,
    )

    assert len(courses) == 1
    assert courses[0].code == "CENG102"
    assert courses[0].name == "Data Structures"
    assert courses[0].gpa_credit == pytest.approx(4.0)
    assert courses[0].ects == pytest.approx(7.0)
    assert courses[0].grade == "BB"
