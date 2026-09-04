from dataclasses import dataclass


@dataclass
class ExtractedCourse:
    """Raw course fields from a parser, before GPA weighting is chosen."""

    code: str
    name: str
    local_credit: float | None
    ects: float | None
    grade: str
    semester: str | None
    # Stable extraction order on the transcript (0-based).
    source_order: int
