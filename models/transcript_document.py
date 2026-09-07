from dataclasses import dataclass, field
from models.extracted_course import ExtractedCourse


@dataclass(frozen=True)
class SummaryObservation:
    """Printed value; source_line is zero-based in normalized extracted text."""
    field_name: str
    value: float
    source_line: int
    label: str
    semester: str | None = None

@dataclass
class StudentInfo:
    university: str | None = None
    faculty: str | None = None
    program: str | None = None

    student_name: str | None = None
    student_number: str | None = None

    enrollment_date: str | None = None
    graduation_date: str | None = None
    graduation_status: str | None = None


@dataclass
class TranscriptSummary:
    """
    Values explicitly reported by the transcript.

    These are not recalculated here.
    Validation/derived calculations will be handled separately.
    """

    cgpa: float | None = None
    total_local_credit: float | None = None
    total_ects: float | None = None
    total_course_count: int | None = None
    semester_count: int | None = None
    graduation_status: str | None = None


@dataclass
class SemesterSummary:
    """
    Values explicitly reported for a semester.
    """

    gpa: float | None = None
    local_credit: float | None = None
    ects: float | None = None
    cgpa: float | None = None


@dataclass
class Semester:
    label: str
    year: str | None = None
    term: str | None = None

    courses: list[ExtractedCourse] = field(default_factory=list)
    course_source_orders: list[int] = field(default_factory=list)
    summary: SemesterSummary | None = None

    source_order: int | None = None


@dataclass
class TranscriptDocument:
    student: StudentInfo = field(default_factory=StudentInfo)
    summary: TranscriptSummary = field(
        default_factory=TranscriptSummary
    )
    semesters: list[Semester] = field(default_factory=list)
    format_name: str | None = None
    confidence: float | None = None
    observations: list[SummaryObservation] = field(default_factory=list)
