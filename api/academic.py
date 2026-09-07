from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas import (
    AcademicSummaryRequest,
    AcademicSummaryResponse,
    CourseImpactCourseResponse,
    CourseImpactOptionResponse,
    CourseImpactRequest,
    CourseImpactResponse,
    FutureSemesterRequest,
    FutureSemesterResponse,
    ManualScenarioChangeResponse,
    ManualScenarioRequest,
    ManualScenarioResponse,
    RequiredSemesterGpaRequest,
    RequiredSemesterGpaResponse,
    SemesterSummaryResponse,
    TargetPlanChangeResponse,
    TargetPlanRequest,
    TargetPlanResponse,
)
from services.academic_summary_service import (
    AcademicSummaryValidationError,
    build_academic_summary,
    validate_and_build_courses,
)
from services.course_impact_service import (
    CourseImpactValidationError,
    build_course_impact,
)
from services.required_gpa_service import (
    RequiredGpaValidationError,
    build_required_semester_gpa,
)
from services.future_semester_service import (
    FutureSemesterValidationError,
    build_future_semester_projection,
    validate_and_build_future_courses,
)
from services.manual_scenario_service import (
    ManualScenarioValidationError,
    build_manual_scenario,
)
from services.target_plan_service import (
    TargetPlanValidationError,
    build_target_plan,
)

router = APIRouter(prefix="/api/academic", tags=["academic"])


@router.post(
    "/summary",
    response_model=AcademicSummaryResponse,
    responses={
        400: {"description": "Invalid academic course data"},
    },
)
def academic_summary(
    payload: AcademicSummaryRequest,
) -> AcademicSummaryResponse:
    try:
        courses = validate_and_build_courses(
            [course.model_dump() for course in payload.courses]
        )
        summary = build_academic_summary(courses, official_cgpa=payload.official_cgpa)
    except AcademicSummaryValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=400,
            detail="Course list contains an unknown grade.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Academic summary could not be calculated.",
        ) from exc

    return AcademicSummaryResponse(
        current_gpa=summary.current_gpa,
        official_cgpa=summary.official_cgpa,
        derived_cgpa=summary.derived_cgpa,
        total_gpa_weight=summary.total_gpa_weight,
        active_course_count=summary.active_course_count,
        semesters=[
            SemesterSummaryResponse(
                semester=row.semester,
                gpa=row.gpa,
                weight=row.weight,
                course_count=row.course_count,
            )
            for row in summary.semesters
        ],
    )


@router.post(
    "/target-plan",
    response_model=TargetPlanResponse,
    responses={
        400: {"description": "Invalid planner request"},
    },
)
def academic_target_plan(
    payload: TargetPlanRequest,
) -> TargetPlanResponse:
    try:
        courses = validate_and_build_courses(
            [course.model_dump() for course in payload.courses]
        )
        plan = build_target_plan(
            courses=courses,
            target_gpa=payload.target_gpa,
            max_grade=payload.max_grade,
            strategy=payload.strategy,
        )
    except (AcademicSummaryValidationError, TargetPlanValidationError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        message = str(exc)
        if message.startswith(
            ("Target GPA", "Invalid strategy", "Invalid maximum")
        ):
            raise HTTPException(
                status_code=400,
                detail=message,
            ) from exc
        raise HTTPException(
            status_code=400,
            detail="Target plan could not be calculated.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Target plan could not be calculated.",
        ) from exc

    return TargetPlanResponse(
        current_gpa=plan.current_gpa,
        target_gpa=plan.target_gpa,
        estimated_gpa=plan.estimated_gpa,
        reachable=plan.reachable,
        already_reached=plan.already_reached,
        strategy=plan.strategy,
        max_grade=plan.max_grade,
        maximum_possible_gpa=plan.maximum_possible_gpa,
        changes=[
            TargetPlanChangeResponse(
                code=change.code,
                name=change.name,
                from_grade=change.from_grade,
                to_grade=change.to_grade,
                gpa_weight=change.gpa_weight,
                gpa_gain=change.gpa_gain,
            )
            for change in plan.changes
        ],
    )


@router.post(
    "/manual-scenario",
    response_model=ManualScenarioResponse,
    responses={
        400: {"description": "Invalid manual scenario request"},
    },
)
def academic_manual_scenario(
    payload: ManualScenarioRequest,
) -> ManualScenarioResponse:
    try:
        courses = validate_and_build_courses(
            [course.model_dump() for course in payload.courses]
        )
        scenario = build_manual_scenario(
            courses=courses,
            raw_changes=[
                change.model_dump() for change in payload.changes
            ],
        )
    except (
        AcademicSummaryValidationError,
        ManualScenarioValidationError,
    ) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Manual scenario could not be calculated.",
        ) from exc

    return ManualScenarioResponse(
        current_gpa=scenario.current_gpa,
        projected_gpa=scenario.projected_gpa,
        gpa_change=scenario.gpa_change,
        changes=[
            ManualScenarioChangeResponse(
                code=change.code,
                name=change.name,
                from_grade=change.from_grade,
                to_grade=change.to_grade,
            )
            for change in scenario.changes
        ],
    )


@router.post(
    "/course-impact",
    response_model=CourseImpactResponse,
    responses={
        400: {"description": "Invalid course impact request"},
    },
)
def academic_course_impact(
    payload: CourseImpactRequest,
) -> CourseImpactResponse:
    try:
        courses = validate_and_build_courses(
            [course.model_dump() for course in payload.courses]
        )
        impact = build_course_impact(
            courses=courses,
            course_code=payload.course_code,
        )
    except (AcademicSummaryValidationError, CourseImpactValidationError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Course impact could not be calculated.",
        ) from exc

    return CourseImpactResponse(
        course=CourseImpactCourseResponse(
            code=impact.course.code,
            name=impact.course.name,
            current_grade=impact.course.current_grade,
            gpa_weight=impact.course.gpa_weight,
        ),
        current_gpa=impact.current_gpa,
        options=[
            CourseImpactOptionResponse(
                grade=option.grade,
                projected_gpa=option.projected_gpa,
                gpa_gain=option.gpa_gain,
            )
            for option in impact.options
        ],
    )


@router.post(
    "/future-semester",
    response_model=FutureSemesterResponse,
    responses={
        400: {"description": "Invalid future semester request"},
    },
)
def academic_future_semester(
    payload: FutureSemesterRequest,
) -> FutureSemesterResponse:
    try:
        current_courses = validate_and_build_courses(
            [course.model_dump() for course in payload.courses]
        )
        future_courses = validate_and_build_future_courses(
            [course.model_dump() for course in payload.future_courses]
        )
        projection = build_future_semester_projection(
            current_courses=current_courses,
            future_courses=future_courses,
        )
    except (
        AcademicSummaryValidationError,
        FutureSemesterValidationError,
    ) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Future semester could not be calculated.",
        ) from exc

    return FutureSemesterResponse(
        current_gpa=projection.current_gpa,
        future_semester_gpa=projection.future_semester_gpa,
        projected_cgpa=projection.projected_cgpa,
        current_gpa_weight=projection.current_gpa_weight,
        future_gpa_weight=projection.future_gpa_weight,
        projected_total_weight=projection.projected_total_weight,
    )


@router.post(
    "/required-semester-gpa",
    response_model=RequiredSemesterGpaResponse,
    responses={
        400: {"description": "Invalid required semester GPA request"},
    },
)
def academic_required_semester_gpa(
    payload: RequiredSemesterGpaRequest,
) -> RequiredSemesterGpaResponse:
    try:
        courses = validate_and_build_courses(
            [course.model_dump() for course in payload.courses]
        )
        result = build_required_semester_gpa(
            courses=courses,
            target_gpa=payload.target_gpa,
            future_gpa_weight=payload.future_gpa_weight,
        )
    except (
        AcademicSummaryValidationError,
        RequiredGpaValidationError,
    ) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        message = str(exc)
        if message.startswith(("Future credits", "Target CGPA")):
            raise HTTPException(
                status_code=400,
                detail=message,
            ) from exc
        raise HTTPException(
            status_code=400,
            detail="Required semester GPA could not be calculated.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Required semester GPA could not be calculated.",
        ) from exc

    return RequiredSemesterGpaResponse(
        current_gpa=result.current_gpa,
        target_gpa=result.target_gpa,
        future_gpa_weight=result.future_gpa_weight,
        required_semester_gpa=result.required_semester_gpa,
        reachable=result.reachable,
        already_reached=result.already_reached,
    )
