"""Legacy public entry points. New ingestion uses parser and service separately."""
from models.course import Course
from parsers.detector import detect_transcript_format
from parsers.formats.cankaya_parser import parse_cankaya_courses
from parsers.formats.generic_parser import parse_generic_courses
from parsers.pdf_extraction import extract_text_from_pdf
from parsers.rows import semester_sort_key
from services.transcript_errors import TranscriptStructureError


def analyze_and_parse_transcript(
    text: str,
    credit_relative_position: int | None = None,
    gpa_weighting_field: str | None = None,
    semantic_field_positions: dict[str, int] | None = None,
):
    """Compatibility wrapper; policy lives in the application service."""
    from services.transcript_workflow import analyze_and_parse_transcript as run
    return run(text, credit_relative_position, gpa_weighting_field, semantic_field_positions)


def parse_courses(
    text: str,
    credit_relative_position: int | None = None
) -> list[Course]:

    detection = detect_transcript_format(
        text
    )

    if detection.format_name == "cankaya":

        return parse_cankaya_courses(
            text
        )

    if detection.requires_credit_selection:

        if credit_relative_position is None:
            raise ValueError(
                "Credit selection is required "
                "for this transcript format."
            )

        return parse_generic_courses(
            text=text,
            credit_relative_position=credit_relative_position
        )

    raise ValueError(
        "Unsupported transcript format."
    )


def keep_latest_attempts(
    courses: list[Course]
) -> list[Course]:
    """
    Keep the latest attempt of each course code for cumulative GPA.

    When every attempt has a dated semester and source_order, compare semester
    dates first (some PDFs list newest semesters first). Otherwise use original
    source_order. JSON array order must not change the API result.

    Fallback for legacy Course objects that have no ``source_order``
    (CLI helpers, older tests, hand-built engines): the last occurrence
    in the current list is treated as latest. That path is order-sensitive
    and is not used for API-originated transcript rows, which carry
    ``source_order`` from extraction.
    """

    dated_codes = {course.code for course in courses}
    for course in courses:
        if course.source_order is None or semester_sort_key(course.semester) is None:
            dated_codes.discard(course.code)

    latest: dict[str, tuple[tuple[int, ...], Course]] = {}

    for index, course in enumerate(courses):
        if course.code in dated_codes:
            rank = (1, *semester_sort_key(course.semester), course.source_order)
        elif course.source_order is not None:
            rank = (1, course.source_order)
        else:
            rank = (0, index)

        previous = latest.get(course.code)
        if previous is None or rank >= previous[0]:
            latest[course.code] = (rank, course)

    return [item[1] for item in latest.values()]
