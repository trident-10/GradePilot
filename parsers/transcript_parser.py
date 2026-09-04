import pdfplumber

from models.course import Course
from models.parse_result import ParseResult
from parsers.credit_options import (
    CreditOption,
    build_credit_options,
    parse_relative_field_key,
    relative_field_key,
)
from parsers.detector import detect_transcript_format
from parsers.formats.cankaya_parser import (
    extract_cankaya_courses,
    parse_cankaya_courses,
)
from parsers.formats.generic_parser import parse_generic_courses
from parsers.generic_analyzer import analyze_generic_transcript
from parsers.gpa_weighting import (
    apply_gpa_weighting,
    build_weighting_options_from_extracted,
)


def extract_text_from_pdf(
    pdf_path: str
) -> str:

    text = ""

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text


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


def _explicit_ects_relative_position(
    credit_options: list[CreditOption],
    selected_credit_position: int
) -> int | None:

    ects_positions = []

    for option in credit_options:

        label = option.label.lower()

        if (
            "akts" not in label
            and "ects" not in label
        ):
            continue

        if option.relative_position is None:
            continue

        if (
            option.relative_position
            == selected_credit_position
        ):
            continue

        if (
            option.relative_position
            not in ects_positions
        ):
            ects_positions.append(
                option.relative_position
            )

    if len(ects_positions) != 1:
        return None

    return ects_positions[0]


def _find_local_credit_option(
    credit_options: list[CreditOption],
) -> CreditOption | None:

    for option in credit_options:
        label = option.label.lower()
        if "akts" in label or "ects" in label:
            continue
        if (
            "kredi" in label
            or "yerel" in label
            or "uk" in label
            or "credit" in label
        ):
            return option

    return None


def _attach_local_credit(
    text: str,
    courses: list[Course],
    credit_options: list[CreditOption],
    selected_relative_position: int,
) -> None:
    """Preserve extracted local credit when a local-credit column exists."""

    local_option = _find_local_credit_option(credit_options)

    if local_option is None or local_option.relative_position is None:
        return

    if local_option.relative_position == selected_relative_position:
        for course in courses:
            course.local_credit = course.gpa_credit
        return

    local_courses = parse_generic_courses(
        text=text,
        credit_relative_position=local_option.relative_position,
    )
    local_by_key = {
        (course.code, course.semester): course
        for course in local_courses
    }

    for course in courses:
        match = local_by_key.get((course.code, course.semester))
        if match is not None:
            course.local_credit = match.gpa_credit


def _resolve_weighting_field(
    gpa_weighting_field: str | None,
    credit_relative_position: int | None,
) -> str | None:

    if gpa_weighting_field is not None:
        return gpa_weighting_field

    if credit_relative_position is not None:
        return relative_field_key(credit_relative_position)

    return None


def _parse_cankaya_result(
    text: str,
    detection_confidence: float,
    gpa_weighting_field: str | None,
) -> ParseResult:

    extracted = extract_cankaya_courses(text)
    credit_options = build_weighting_options_from_extracted(
        extracted
    )

    if gpa_weighting_field is None:
        warnings = [
            "GANO hesabında hangi değerin kullanılacağını seçmelisiniz."
        ]

        if not credit_options:
            warnings.append(
                "Transkriptte Kredi veya AKTS/ECTS alanı "
                "tespit edilemedi."
            )

        return ParseResult(
            courses=[],
            format_name="cankaya",
            confidence=detection_confidence,
            requires_user_confirmation=False,
            requires_credit_selection=True,
            warnings=warnings,
            credit_options=credit_options,
        )

    if gpa_weighting_field not in {
        option.field_key for option in credit_options
    }:
        raise ValueError(
            f"Unsupported GPA weighting field for Cankaya: "
            f"{gpa_weighting_field}"
        )

    courses = apply_gpa_weighting(
        extracted,
        gpa_weighting_field,
    )

    return ParseResult(
        courses=courses,
        format_name="cankaya",
        confidence=detection_confidence,
        requires_user_confirmation=False,
        requires_credit_selection=False,
        warnings=[],
        credit_options=None,
    )


def _parse_generic_result(
    text: str,
    detection_confidence: float,
    gpa_weighting_field: str | None,
) -> ParseResult:

    analysis = analyze_generic_transcript(text)
    credit_options = build_credit_options(analysis)

    if gpa_weighting_field is None:
        warnings = [
            "The transcript format was not recognized. "
            "The GPA credit field must be selected."
        ]

        if not credit_options:
            warnings.append(
                "No viable credit columns were found. "
                "A credit column will not be guessed."
            )

        return ParseResult(
            courses=[],
            format_name="generic",
            confidence=detection_confidence,
            requires_user_confirmation=True,
            requires_credit_selection=True,
            warnings=warnings,
            credit_options=credit_options,
        )

    selected_relative_position = parse_relative_field_key(
        gpa_weighting_field
    )

    if selected_relative_position is None:
        raise ValueError(
            f"Unsupported GPA weighting field for generic "
            f"transcript: {gpa_weighting_field}"
        )

    ects_relative_position = _explicit_ects_relative_position(
        credit_options=credit_options,
        selected_credit_position=selected_relative_position,
    )

    courses = parse_generic_courses(
        text=text,
        credit_relative_position=selected_relative_position,
        ects_relative_position=ects_relative_position,
    )

    _attach_local_credit(
        text=text,
        courses=courses,
        credit_options=credit_options,
        selected_relative_position=selected_relative_position,
    )

    # If user selected the local-credit column, ensure local_credit is set.
    selected_option = next(
        (
            option
            for option in credit_options
            if option.field_key == gpa_weighting_field
        ),
        None,
    )
    if (
        selected_option is not None
        and selected_option.label == "Kredi"
    ):
        for course in courses:
            if course.local_credit is None:
                course.local_credit = course.gpa_credit

    warnings = [
        "Generic parsing was used. "
        "The extracted course information "
        "must be confirmed."
    ]

    if not courses:
        warnings.append(
            "No courses were extracted for "
            "the selected credit field."
        )

    return ParseResult(
        courses=courses,
        format_name="generic",
        confidence=detection_confidence,
        requires_user_confirmation=True,
        requires_credit_selection=False,
        warnings=warnings,
        credit_options=None,
    )


def analyze_and_parse_transcript(
    text: str,
    credit_relative_position: int | None = None,
    gpa_weighting_field: str | None = None,
) -> ParseResult:

    detection = detect_transcript_format(text)
    resolved_field = _resolve_weighting_field(
        gpa_weighting_field=gpa_weighting_field,
        credit_relative_position=credit_relative_position,
    )

    if detection.format_name == "cankaya":
        return _parse_cankaya_result(
            text=text,
            detection_confidence=detection.confidence,
            gpa_weighting_field=resolved_field,
        )

    return _parse_generic_result(
        text=text,
        detection_confidence=detection.confidence,
        gpa_weighting_field=resolved_field,
    )


def keep_latest_attempts(
    courses: list[Course]
) -> list[Course]:
    """
    Keep the latest attempt of each course code for cumulative GPA.

    Latest is determined by ``source_order`` (original parser/transcript
    extraction order). A higher ``source_order`` is later on the transcript.
    JSON array order from the frontend must not change this result.

    Fallback for legacy Course objects that have no ``source_order``
    (CLI helpers, older tests, hand-built engines): the last occurrence
    in the current list is treated as latest. That path is order-sensitive
    and is not used for API-originated transcript rows, which carry
    ``source_order`` from extraction.
    """

    latest: dict[str, tuple[tuple[int, int], Course]] = {}

    for index, course in enumerate(courses):
        if course.source_order is not None:
            rank = (1, course.source_order)
        else:
            rank = (0, index)

        previous = latest.get(course.code)
        if previous is None or rank >= previous[0]:
            latest[course.code] = (rank, course)

    return [item[1] for item in latest.values()]
