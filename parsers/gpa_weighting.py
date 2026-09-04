from models.course import Course
from models.extracted_course import ExtractedCourse
from parsers.credit_options import CreditOption

FIELD_LOCAL_CREDIT = "local_credit"
FIELD_ECTS = "ects"


def build_weighting_options_from_extracted(
    extracted_courses: list[ExtractedCourse],
) -> list[CreditOption]:
    """Offer only credit fields that were actually extracted."""

    options: list[CreditOption] = []

    local_values = [
        course.local_credit
        for course in extracted_courses
        if course.local_credit is not None
    ]
    ects_values = [
        course.ects
        for course in extracted_courses
        if course.ects is not None
    ]

    if local_values:
        options.append(
            CreditOption(
                label="Kredi",
                field_key=FIELD_LOCAL_CREDIT,
                sample_values=local_values[:5],
                score=1.0,
                relative_position=None,
            )
        )

    if ects_values:
        options.append(
            CreditOption(
                label="AKTS / ECTS",
                field_key=FIELD_ECTS,
                sample_values=ects_values[:5],
                score=1.0,
                relative_position=None,
            )
        )

    return options


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
