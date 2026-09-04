import re

from models.course import Course


GRADE_PATTERN = re.compile(
    r"\b(AA|BA|BB|CB|CC|DC|DD|FD|FF)\b"
)


def _find_grade_index(
    parts: list[str]
) -> int | None:

    for index, part in enumerate(parts):

        if GRADE_PATTERN.fullmatch(part):
            return index

    return None


def _float_at_relative_position(
    parts: list[str],
    grade_index: int,
    relative_position: int
) -> float | None:

    token_index = (
        grade_index + relative_position
    )

    if (
        token_index < 0
        or token_index >= len(parts)
    ):
        return None

    try:
        return float(
            parts[token_index]
        )
    except ValueError:
        return None


def _extract_course_name(
    parts: list[str],
    grade_index: int,
    credit_index: int | None,
    ects_index: int | None
) -> str:

    name_end = grade_index

    if credit_index is not None:
        name_end = min(
            name_end,
            credit_index
        )

    if ects_index is not None:
        name_end = min(
            name_end,
            ects_index
        )

    if name_end <= 1:
        return ""

    name_tokens = parts[1:name_end]

    if credit_index is None:

        while name_tokens:

            try:
                float(name_tokens[-1])
            except ValueError:
                break

            name_tokens.pop()

    if not name_tokens:
        return ""

    return " ".join(name_tokens)


def _is_department_prefix(
    token: str
) -> bool:

    return (
        len(token) >= 2
        and token.isalpha()
    )


def _is_course_number(
    token: str
) -> bool:

    return (
        token.isdigit()
        and 2 <= len(token) <= 4
    )


def _combine_split_course_code(
    parts: list[str]
) -> list[str]:

    if len(parts) < 2:
        return parts

    prefix = parts[0]
    number = parts[1]

    if not (
        _is_department_prefix(prefix)
        and _is_course_number(number)
    ):
        return parts

    combined_code = prefix + number

    return [
        combined_code,
        *parts[2:],
    ]


def parse_generic_courses(
    text: str,
    credit_mode: str | None = None,
    credit_relative_position: int | None = None,
    ects_relative_position: int | None = None
) -> list[Course]:

    if (
        credit_mode is None
        and credit_relative_position is None
    ):
        raise ValueError(
            "Credit mode selection is required "
            "for unknown transcript formats."
        )

    courses = []

    for line in text.splitlines():

        grade_match = GRADE_PATTERN.search(
            line
        )

        if not grade_match:
            continue

        parts = line.split()

        if len(parts) < 4:
            continue

        parts = _combine_split_course_code(
            parts
        )

        if len(parts) < 4:
            continue

        course_code = parts[0]

        grade = grade_match.group(1)

        grade_index = _find_grade_index(
            parts
        )

        credit_index = None
        ects_index = None
        ects = None

        if credit_relative_position is not None:

            if grade_index is None:
                continue

            credit_index = (
                grade_index
                + credit_relative_position
            )

            gpa_credit = _float_at_relative_position(
                parts=parts,
                grade_index=grade_index,
                relative_position=(
                    credit_relative_position
                ),
            )

            if gpa_credit is None:
                continue

        else:
            numeric_values = []

            for part in parts:

                try:
                    numeric_values.append(
                        float(part)
                    )
                except ValueError:
                    continue

            if not numeric_values:
                continue

            if credit_mode == "first_numeric":
                gpa_credit = numeric_values[0]

            elif credit_mode == "last_numeric":
                gpa_credit = numeric_values[-1]

            else:
                raise ValueError(
                    f"Unsupported credit mode: {credit_mode}"
                )

        if (
            ects_relative_position is not None
            and grade_index is not None
        ):
            ects_index = (
                grade_index
                + ects_relative_position
            )

            ects = _float_at_relative_position(
                parts=parts,
                grade_index=grade_index,
                relative_position=(
                    ects_relative_position
                ),
            )

        if grade_index is None:
            course_name = line
        else:
            course_name = _extract_course_name(
                parts=parts,
                grade_index=grade_index,
                credit_index=credit_index,
                ects_index=ects_index,
            )

        courses.append(
            Course(
                code=course_code,
                name=course_name,
                gpa_credit=gpa_credit,
                ects=ects,
                grade=grade,
                semester=None,
                source_order=len(courses),
            )
        )

    return courses
