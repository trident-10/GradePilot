from models.course import Course
from models.extracted_course import ExtractedCourse
from parsers.semantic_fields import FIELD_ECTS, FIELD_LOCAL_CREDIT


def build_weighting_options_from_extracted(extracted_courses):
    """Compatibility helper; user-facing options belong to presentation."""
    from services.transcript_presentation import build_weighting_options_from_extracted as build
    return build(extracted_courses)


def apply_gpa_weighting(
    extracted_courses: list[ExtractedCourse],
    field_key: str,
) -> list[Course]:
    """Map extracted rows to Course, setting gpa_credit from the chosen field."""

    if field_key not in (FIELD_LOCAL_CREDIT, FIELD_ECTS):
        raise ValueError(
            f"Unsupported GPA weighting field: {field_key}"
        )

    courses: list[Course] = []

    for extracted in extracted_courses:
        if field_key == FIELD_LOCAL_CREDIT:
            if extracted.local_credit is None:
                continue
            gpa_credit = extracted.local_credit
        else:
            if extracted.ects is None:
                continue
            gpa_credit = extracted.ects

        courses.append(
            Course(
                code=extracted.code,
                name=extracted.name,
                gpa_credit=gpa_credit,
                grade=extracted.grade,
                semester=extracted.semester,
                ects=extracted.ects,
                local_credit=extracted.local_credit,
                source_order=extracted.source_order,
            )
        )

    return courses
