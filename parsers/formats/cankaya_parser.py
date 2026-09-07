from models.course import Course
from models.extracted_course import ExtractedCourse
from parsers.gpa_weighting import FIELD_LOCAL_CREDIT, apply_gpa_weighting
from parsers.rows import course_name, fold, number, read_rows


def extract_cankaya_courses(text: str, *, rows=None) -> list[ExtractedCourse]:
    """Recognize the known type/language/hours/credit/ECTS schema per row."""
    courses = []
    for order, row in enumerate(read_rows(text) if rows is None else rows):
        index = row.grade_index
        if index is None or index < 8:
            continue
        # The institution name alone does not prove a particular table layout.
        if row.parts[index - 6] not in {"Z", "S"}:
            continue
        if fold(row.parts[index - 5]).rstrip(".") not in {"ing", "tr", "tur", "eng", "en"}:
            continue
        numeric = [number(part) for part in row.parts[index - 4:index]]
        if any(value is None or value < 0 for value in numeric):
            continue
        courses.append(ExtractedCourse(
            code=row.parts[0], name=course_name(row),
            local_credit=numeric[2], ects=numeric[3], grade=row.parts[index],
            semester=row.semester, source_order=order,
        ))
    return courses


def parse_cankaya_courses(text: str) -> list[Course]:
    """Legacy helper using local credit; product flow asks for weighting."""
    return apply_gpa_weighting(extract_cankaya_courses(text), FIELD_LOCAL_CREDIT)
