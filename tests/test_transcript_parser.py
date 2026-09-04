from models.course import Course
from parsers.formats.cankaya_parser import parse_cankaya_courses
from parsers.transcript_parser import (
    parse_courses,
    keep_latest_attempts,
)


def test_parse_courses():
    """Low-level Cankaya extractor still maps local credit by default."""

    text = """
Çankaya University
2024-2025 Güz Dönemi
CENG 111 Bilgisayar Programlama I Z İng. 3 2 4 6 DD 1.00
MATH 157 Genel Matematik I Z Tr 3 2 4 6 BB 3.00
"""

    courses = parse_courses(text)

    assert courses[0].gpa_credit == 4.0
    assert courses[0].ects == 6.0
    assert courses[0].local_credit == 4.0

    assert len(courses) == 2

    assert courses[0].code == "CENG111"

    assert courses[0].name == "Bilgisayar Programlama I"

    assert courses[0].gpa_credit == 4.0

    assert courses[0].grade == "DD"

    assert courses[0].semester == "2024-2025 Güz"


def test_parse_cankaya_courses_preserves_both_fields():
    text = """
Çankaya University
2024-2025 Güz Dönemi
CENG 111 Bilgisayar Programlama I Z İng. 3 2 4 6 DD 1.00
"""

    courses = parse_cankaya_courses(text)

    assert courses[0].local_credit == 4.0
    assert courses[0].ects == 6.0
    assert courses[0].gpa_credit == 4.0


def test_keep_latest_attempt():

    text = """
Çankaya University
2024-2025 Güz Dönemi
CENG 111 Bilgisayar Programlama I Z İng. 3 2 4 6 DD 1.00

2025-2026 Güz Dönemi
CENG 111 Bilgisayar Programlama I Z İng. 3 2 4 6 BA 3.50
"""

    courses = parse_courses(text)

    latest_courses = keep_latest_attempts(
        courses
    )

    assert len(courses) == 2

    assert len(latest_courses) == 1

    assert latest_courses[0].code == "CENG111"

    assert latest_courses[0].grade == "BA"

    assert latest_courses[0].semester == "2025-2026 Güz"
    assert courses[0].source_order == 0
    assert courses[1].source_order == 1

    reversed_latest = keep_latest_attempts(list(reversed(courses)))
    assert len(reversed_latest) == 1
    assert reversed_latest[0].grade == "BA"


def test_keep_latest_uses_source_order_not_list_position():
    older = Course(
        code="CENG111",
        name="Programming",
        gpa_credit=4,
        grade="DD",
        semester="2024-2025 Güz",
        source_order=4,
    )
    newer = Course(
        code="CENG111",
        name="Programming",
        gpa_credit=4,
        grade="BA",
        semester="2025-2026 Güz",
        source_order=19,
    )

    for sequence in ([older, newer], [newer, older]):
        latest = keep_latest_attempts(sequence)
        assert len(latest) == 1
        assert latest[0].grade == "BA"
        assert latest[0].source_order == 19


def test_keep_latest_fallback_uses_list_order_without_source_order():
    older = Course(
        code="CENG111",
        name="Programming",
        gpa_credit=4,
        grade="DD",
        semester="2024-2025 Güz",
    )
    newer = Course(
        code="CENG111",
        name="Programming",
        gpa_credit=4,
        grade="BA",
        semester="2025-2026 Güz",
    )

    latest = keep_latest_attempts([newer, older])
    assert latest[0].grade == "DD"