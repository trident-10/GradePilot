from models.course import Course
from models.extracted_course import ExtractedCourse
from parsers.rows import GRADE_PATTERN, course_name, number, read_rows


def _float_at_relative_position(parts, grade_index, relative_position):
    index = grade_index + relative_position
    if index < 1 or index >= len(parts):
        return None
    value = number(parts[index])
    return value if value is not None and value >= 0 else None


def extract_generic_courses(
    text: str,
    local_credit_relative_position: int | None = None,
    ects_relative_position: int | None = None,
    *,
    use_row_headers: bool = False,
    rows=None,
) -> list[ExtractedCourse]:
    """Extract both credit fields using the same rows as column analysis."""
    if local_credit_relative_position is None and ects_relative_position is None:
        raise ValueError("At least one semantic credit field is required for generic transcript extraction.")
    courses = []
    for order, row in enumerate(read_rows(text) if rows is None else rows):
        grade_index = row.grade_index
        if grade_index is None:
            continue
        positions = {
            "local_credit": local_credit_relative_position,
            "ects": ects_relative_position,
        }
        if use_row_headers and row.field_positions is not None:
            positions = row.field_positions
        values = {
            field: _float_at_relative_position(row.parts, grade_index, position)
            if position is not None else None
            for field, position in positions.items()
        }
        if all(value is None for value in values.values()):
            continue
        courses.append(ExtractedCourse(
            code=row.parts[0], name=course_name(row, positions),
            local_credit=values.get("local_credit"), ects=values.get("ects"),
            grade=row.parts[grade_index], semester=row.semester,
            source_order=order,
        ))
    return courses


def parse_generic_courses(
    text: str,
    credit_mode: str | None = None,
    credit_relative_position: int | None = None,
    ects_relative_position: int | None = None,
) -> list[Course]:
    """Legacy helper; product flow uses explicit semantic field selection."""
    if credit_relative_position is not None:
        from parsers.gpa_weighting import apply_gpa_weighting
        return apply_gpa_weighting(extract_generic_courses(
            text, credit_relative_position, ects_relative_position,
        ), "local_credit")
    if credit_mode is None:
        raise ValueError("Credit mode selection is required for unknown transcript formats.")
    if credit_mode not in {"first_numeric", "last_numeric"}:
        raise ValueError(f"Unsupported credit mode: {credit_mode}")
    courses = []
    for order, row in enumerate(read_rows(text)):
        grade_index = row.grade_index
        values = [value for part in row.parts[1:] if (value := number(part)) is not None]
        if grade_index is None or not values:
            continue
        courses.append(Course(
            code=row.parts[0], name=course_name(row),
            gpa_credit=values[0 if credit_mode == "first_numeric" else -1],
            grade=row.parts[grade_index], semester=row.semester, source_order=order,
            ects=_float_at_relative_position(row.parts, grade_index, ects_relative_position)
            if ects_relative_position is not None else None,
        ))
    return courses
