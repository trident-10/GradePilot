from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CreditOptionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Public weighting field id, e.g. credit or ects")
    label: str


class MappingCandidateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Opaque public numeric column id")
    label: str
    sample_values: list[float] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"]


class CourseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    name: str
    gpa_credit: float
    ects: float | None = None
    local_credit: float | None = None
    grade: str
    semester: str | None = None
    source_order: int


class OfficialTranscriptSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cgpa: float | None = None
    total_local_credit: float | None = None
    total_ects: float | None = None
    total_course_count: int | None = None
    semester_count: int | None = None
    graduation_status: str | None = None


class OfficialSemesterSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gpa: float | None = None
    cgpa: float | None = None
    local_credit: float | None = None
    ects: float | None = None


class TranscriptSemesterResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str
    year: str | None = None
    term: str | None = None
    course_source_orders: list[int] = Field(default_factory=list)
    official_summary: OfficialSemesterSummaryResponse | None = None


class TranscriptAnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal[
        "manual_mapping",
        "credit_selection",
        "confirmation",
        "ready",
    ]
    format: str
    confidence: float
    credit_options: list[CreditOptionResponse] = Field(default_factory=list)
    mapping_candidates: list[MappingCandidateResponse] = Field(
        default_factory=list
    )
    courses: list[CourseResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    official_summary: OfficialTranscriptSummaryResponse | None = None
    semesters: list[TranscriptSemesterResponse] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detail: str


class TranscriptIngestionErrorResponse(ErrorResponse):
    error_type: Literal["invalid_transcript", "invalid_mapping_request"] | None = None
    code: str | None = None


class CourseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    name: str
    gpa_credit: float
    grade: str
    semester: str | None = None
    ects: float | None = None
    local_credit: float | None = None
    source_order: int | None = None


class AcademicSummaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    courses: list[CourseInput]
    official_cgpa: float | None = Field(default=None, ge=0, le=4, strict=True, allow_inf_nan=False)


class SemesterSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    semester: str
    gpa: float
    weight: float
    course_count: int


class AcademicSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_gpa: float = Field(description="Legacy derived GPA; unchanged for calculation consumers")
    official_cgpa: float | None = None
    derived_cgpa: float
    total_gpa_weight: float
    active_course_count: int
    semesters: list[SemesterSummaryResponse] = Field(default_factory=list)


class TargetPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    courses: list[CourseInput]
    target_gpa: float
    max_grade: str
    strategy: str


class TargetPlanChangeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    name: str
    from_grade: str
    to_grade: str
    gpa_weight: float
    gpa_gain: float | None = None


class TargetPlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_gpa: float
    target_gpa: float
    estimated_gpa: float
    reachable: bool
    already_reached: bool
    strategy: str
    max_grade: str
    maximum_possible_gpa: float | None = None
    changes: list[TargetPlanChangeResponse] = Field(default_factory=list)


class ManualScenarioChangeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    course_code: str
    new_grade: str


class ManualScenarioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    courses: list[CourseInput]
    changes: list[ManualScenarioChangeInput]


class ManualScenarioChangeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    name: str
    from_grade: str
    to_grade: str


class ManualScenarioResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_gpa: float
    projected_gpa: float
    gpa_change: float
    changes: list[ManualScenarioChangeResponse] = Field(default_factory=list)


class CourseImpactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    courses: list[CourseInput]
    course_code: str


class CourseImpactCourseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    name: str
    current_grade: str
    gpa_weight: float


class CourseImpactOptionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grade: str
    projected_gpa: float
    gpa_gain: float


class CourseImpactResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    course: CourseImpactCourseResponse
    current_gpa: float
    options: list[CourseImpactOptionResponse] = Field(default_factory=list)


class FutureCourseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    gpa_credit: float
    grade: str
    code: str | None = None


class FutureSemesterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    courses: list[CourseInput]
    future_courses: list[FutureCourseInput]


class FutureSemesterResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_gpa: float
    future_semester_gpa: float
    projected_cgpa: float
    current_gpa_weight: float
    future_gpa_weight: float
    projected_total_weight: float


class RequiredSemesterGpaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    courses: list[CourseInput]
    target_gpa: float
    future_gpa_weight: float


class RequiredSemesterGpaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_gpa: float
    target_gpa: float
    future_gpa_weight: float
    required_semester_gpa: float
    reachable: bool
    already_reached: bool
