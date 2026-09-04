from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CreditOptionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Public weighting field id, e.g. credit or ects")
    label: str


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


class TranscriptAnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["credit_selection", "confirmation", "ready"]
    format: str
    confidence: float
    credit_options: list[CreditOptionResponse] = Field(default_factory=list)
    courses: list[CourseResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detail: str


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


class SemesterSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    semester: str
    gpa: float
    weight: float
    course_count: int


class AcademicSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_gpa: float
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
