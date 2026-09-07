from __future__ import annotations

from dataclasses import dataclass
import math

from core.gpa_engine import calculate_gpa
from core.grade_scale import GRADE_POINTS
from core.semester_engine import calculate_semester_gpas
from models.course import Course
from parsers.transcript_parser import keep_latest_attempts


class AcademicSummaryValidationError(ValueError):
    """Raised when client-provided course data is invalid for calculation."""


@dataclass(frozen=True)
class SemesterSummary:
    semester: str
    gpa: float
    weight: float
    course_count: int


@dataclass(frozen=True)
class AcademicSummary:
    current_gpa: float
    total_gpa_weight: float
    active_course_count: int
    semesters: list[SemesterSummary]
    official_cgpa: float | None
    derived_cgpa: float


def validate_and_build_courses(
    raw_courses: list[dict],
) -> list[Course]:
    """Validate request course dicts and build Course models."""

    if not isinstance(raw_courses, list):
        raise AcademicSummaryValidationError(
            "Course list is required."
        )

    if len(raw_courses) == 0:
        raise AcademicSummaryValidationError(
            "No courses were provided."
        )

    courses: list[Course] = []

    for index, item in enumerate(raw_courses, start=1):
        if not isinstance(item, dict):
            raise AcademicSummaryValidationError(
                f"Course #{index} is invalid."
            )

        code = item.get("code")
        name = item.get("name")
        grade = item.get("grade")
        gpa_credit = item.get("gpa_credit")
        semester = item.get("semester")
        source_order = item.get("source_order")
        ects = item.get("ects")
        local_credit = item.get("local_credit")

        if not isinstance(code, str) or not code.strip():
            raise AcademicSummaryValidationError(
                f"Course #{index} is missing a valid code."
            )

        if not isinstance(name, str) or not name.strip():
            raise AcademicSummaryValidationError(
                f"Course #{index} is missing a valid name."
            )

        if not isinstance(grade, str) or grade not in GRADE_POINTS:
            raise AcademicSummaryValidationError(
                f"Course #{index} has an unknown grade."
            )

        if not isinstance(gpa_credit, (int, float)):
            raise AcademicSummaryValidationError(
                f"Course #{index} has an invalid GPA weight."
            )

        if gpa_credit < 0:
            raise AcademicSummaryValidationError(
                f"Course #{index} has a negative GPA weight."
            )

        if semester is not None and not isinstance(semester, str):
            raise AcademicSummaryValidationError(
                f"Course #{index} has an invalid semester value."
            )

        if ects is not None and not isinstance(ects, (int, float)):
            raise AcademicSummaryValidationError(
                f"Course #{index} has an invalid ECTS value."
            )

        if local_credit is not None and not isinstance(
            local_credit, (int, float)
        ):
            raise AcademicSummaryValidationError(
                f"Course #{index} has an invalid local credit value."
            )

        if local_credit is not None and local_credit < 0:
            raise AcademicSummaryValidationError(
                f"Course #{index} has a negative local credit value."
            )

        if source_order is not None:
            if isinstance(source_order, bool) or not isinstance(
                source_order, int
            ):
                raise AcademicSummaryValidationError(
                    f"Course #{index} has an invalid source order."
                )
            if source_order < 0:
                raise AcademicSummaryValidationError(
                    f"Course #{index} has an invalid source order."
                )

        normalized_semester = semester.strip() if isinstance(semester, str) else None
        if normalized_semester == "":
            normalized_semester = None

        courses.append(
            Course(
                code=code.strip(),
                name=name.strip(),
                gpa_credit=float(gpa_credit),
                grade=grade,
                semester=normalized_semester,
                ects=float(ects) if ects is not None else None,
                local_credit=(
                    float(local_credit) if local_credit is not None else None
                ),
                source_order=source_order,
            )
        )

    return courses


def validate_official_cgpa(official_cgpa: float | None) -> float | None:
    if official_cgpa is None:
        return None
    if (
        isinstance(official_cgpa, bool)
        or not isinstance(official_cgpa, (int, float))
        or not math.isfinite(official_cgpa)
        or not 0 <= official_cgpa <= 4
    ):
        raise AcademicSummaryValidationError("Official CGPA must be between 0.00 and 4.00.")
    return float(official_cgpa)


def build_academic_summary(
    courses: list[Course], *, official_cgpa: float | None = None,
) -> AcademicSummary:
    """
    Cumulative GANO uses latest attempts.
    Semester GPAs use historical attempts as returned by calculate_semester_gpas.
    Official CGPA is kept separately as derived_cgpa's peer; current_gpa is the
    planning baseline (official when present, otherwise course-derived).
    """

    official = validate_official_cgpa(official_cgpa)
    active_courses = keep_latest_attempts(courses)
    derived = float(calculate_gpa(active_courses))
    total_gpa_weight = sum(
        course.gpa_credit for course in active_courses
    )

    semester_rows = calculate_semester_gpas(courses)
    semesters = [
        SemesterSummary(
            semester=row["semester"],
            gpa=float(row["gpa"]),
            weight=float(row["credits"]),
            course_count=int(row["course_count"]),
        )
        for row in semester_rows
    ]

    return AcademicSummary(
        current_gpa=official if official is not None else derived,
        total_gpa_weight=float(total_gpa_weight),
        active_course_count=len(active_courses),
        semesters=semesters,
        official_cgpa=official,
        derived_cgpa=derived,
    )
