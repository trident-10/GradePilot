from __future__ import annotations

from dataclasses import dataclass

from core.gpa_engine import calculate_gpa
from core.grade_scale import GRADE_POINTS
from core.scenario_engine import simulate_grade_change
from core.target_engine import VALID_STRATEGIES, find_target_plan
from models.course import Course
from parsers.transcript_parser import keep_latest_attempts
from services.academic_summary_service import AcademicSummaryValidationError


class TargetPlanValidationError(AcademicSummaryValidationError):
    """Raised when target-plan request data is invalid."""


@dataclass(frozen=True)
class TargetPlanChange:
    code: str
    name: str
    from_grade: str
    to_grade: str
    gpa_weight: float
    gpa_gain: float | None


@dataclass(frozen=True)
class TargetPlan:
    current_gpa: float
    target_gpa: float
    estimated_gpa: float
    reachable: bool
    already_reached: bool
    strategy: str
    max_grade: str
    maximum_possible_gpa: float | None
    changes: list[TargetPlanChange]


def _validate_planner_inputs(
    target_gpa: object,
    max_grade: object,
    strategy: object,
) -> tuple[float, str, str]:
    if isinstance(target_gpa, bool) or not isinstance(target_gpa, (int, float)):
        raise TargetPlanValidationError(
            "Target GPA must be between 0.00 and 4.00"
        )

    numeric_target = float(target_gpa)
    if numeric_target != numeric_target:  # NaN
        raise TargetPlanValidationError(
            "Target GPA must be between 0.00 and 4.00"
        )
    if not 0.0 <= numeric_target <= 4.0:
        raise TargetPlanValidationError(
            "Target GPA must be between 0.00 and 4.00"
        )

    if not isinstance(max_grade, str) or max_grade not in GRADE_POINTS:
        raise TargetPlanValidationError("Invalid maximum grade.")

    if not isinstance(strategy, str) or strategy not in VALID_STRATEGIES:
        raise TargetPlanValidationError("Invalid strategy.")

    return numeric_target, max_grade, strategy


def build_target_plan(
    courses: list[Course],
    target_gpa: object,
    max_grade: object,
    strategy: object,
) -> TargetPlan:
    """
    Cumulative planner uses latest attempts (source_order).
    find_target_plan remains the source of truth for strategy results.
    """

    numeric_target, grade, selected_strategy = _validate_planner_inputs(
        target_gpa,
        max_grade,
        strategy,
    )

    active_courses = keep_latest_attempts(courses)
    total_weight = sum(course.gpa_credit for course in active_courses)
    if total_weight == 0:
        raise TargetPlanValidationError("No GPA weight was provided.")

    engine_result = find_target_plan(
        courses=active_courses,
        target_gpa=numeric_target,
        strategy=selected_strategy,
        max_grade=grade,
    )

    current_gpa = calculate_gpa(active_courses)
    estimated_gpa = float(engine_result["projected_gpa"])
    reachable = bool(engine_result["reachable"])
    already_reached = bool(engine_result["already_reached"])

    changes: list[TargetPlanChange] = []
    for item in engine_result["plan"]:
        code = str(item["course_code"])
        to_grade = str(item["new_grade"])
        gpa_gain: float | None
        try:
            simulation = simulate_grade_change(
                active_courses,
                code,
                to_grade,
            )
            gpa_gain = float(simulation["difference"])
        except ValueError:
            gpa_gain = None

        changes.append(
            TargetPlanChange(
                code=code,
                name=str(item["course_name"]),
                from_grade=str(item["old_grade"]),
                to_grade=to_grade,
                gpa_weight=float(item["credit"]),
                gpa_gain=gpa_gain,
            )
        )

    return TargetPlan(
        current_gpa=float(current_gpa),
        target_gpa=numeric_target,
        estimated_gpa=estimated_gpa,
        reachable=reachable,
        already_reached=already_reached,
        strategy=selected_strategy,
        max_grade=grade,
        maximum_possible_gpa=None if reachable else estimated_gpa,
        changes=changes,
    )
