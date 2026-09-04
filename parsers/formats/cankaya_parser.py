import re

from models.course import Course
from models.extracted_course import ExtractedCourse
from parsers.gpa_weighting import (
    FIELD_LOCAL_CREDIT,
    apply_gpa_weighting,
)


def extract_cankaya_courses(
    text: str
) -> list[ExtractedCourse]:
    """Extract Cankaya rows with both local credit and ECTS preserved."""

    courses: list[ExtractedCourse] = []
    current_semester = None

    semester_pattern = re.compile(
        r"(\d{4}-\d{4}) (Güz|Bahar) Dönemi"
    )

    course_pattern = re.compile(
        r"^([A-Z]+)\s+(\d+)\s+(.+?)\s+[ZS]\s+(?:İng\.|Tr)\s+"
        r"\d+\s+\d+\s+(\d+)\s+(\d+)\s+"
        r"(AA|BA|BB|CB|CC|DC|DD|FD|FF)\s+"
    )

    for line in text.splitlines():
        semester_match = semester_pattern.search(line)

        if semester_match:
            current_semester = (
                f"{semester_match.group(1)} "
                f"{semester_match.group(2)}"
            )
            continue

        course_match = course_pattern.match(line)

        if course_match:
            code = (
                course_match.group(1)
                + course_match.group(2)
            )
            name = course_match.group(3)
            local_credit = float(course_match.group(4))
            ects = float(course_match.group(5))
            grade = course_match.group(6)

            courses.append(
                ExtractedCourse(
                    code=code,
                    name=name,
                    local_credit=local_credit,
                    ects=ects,
                    grade=grade,
                    semester=current_semester,
                    source_order=len(courses),
                )
            )

    return courses


def parse_cankaya_courses(
    text: str
) -> list[Course]:
    """
    Legacy helper: extract Cankaya courses using local credit as gpa_credit.

    Product flow should use extract_cankaya_courses + user weighting selection
    via analyze_and_parse_transcript instead of calling this directly.
    """

    return apply_gpa_weighting(
        extract_cankaya_courses(text),
        FIELD_LOCAL_CREDIT,
    )
