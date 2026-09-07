from models.course import Course
from core.gpa_baseline import anchored_current
from core.grade_scale import GRADE_POINTS
GRADE_ORDER = [
    "FF",
    "FD",
    "DD",
    "DC",
    "CC",
    "CB",
    "BB",
    "BA",
    "AA",
]

VALID_STRATEGIES = {
    "min_courses",
    "lowest_grades",
    "minimal_change",
}


def analyze_target_gpa(
    courses: list[Course],
    target_gpa: float,
    official_cgpa: float | None = None,
) -> dict:

    if not 0.0 <= target_gpa <= 4.0:
        raise ValueError(
            "Target GPA must be between 0.00 and 4.00"
        )

    current_gpa, current_points, total_credits = anchored_current(
        courses, official_cgpa
    )

    target_points = target_gpa * total_credits

    required_points = target_points - current_points

    return {
        "current_gpa": current_gpa,
        "target_gpa": target_gpa,
        "total_credits": total_credits,
        "current_points": current_points,
        "target_points": target_points,
        "required_points": max(0, required_points),
        "already_reached": current_gpa >= target_gpa,
    }


def build_improvement_options(
    courses: list[Course],
    max_grade: str
) -> list[dict]:

    if max_grade not in GRADE_POINTS:
        raise ValueError(
            f"Invalid maximum grade: {max_grade}"
        )

    max_grade_point = GRADE_POINTS[max_grade]

    options = []

    for course in courses:

        current_grade_point = GRADE_POINTS[
            course.grade
        ]

        # Mevcut not zaten belirlenen maksimum
        # nottan yüksek veya eşitse bu dersi atla.
        if current_grade_point >= max_grade_point:
            continue

        point_gain = (
            max_grade_point - current_grade_point
        ) * course.gpa_credit

        options.append({
            "course_code": course.code,
            "course_name": course.name,
            "credit": course.gpa_credit,
            "old_grade": course.grade,
            "new_grade": max_grade,
            "point_gain": point_gain,
        })

    return options


def find_minimal_change_plan(
    courses: list[Course],
    required_points: float,
    max_grade: str
) -> dict:

    max_grade_index = GRADE_ORDER.index(
        max_grade
    )

    upgrades = []

    for course in courses:

        current_index = GRADE_ORDER.index(
            course.grade
        )

        if current_index >= max_grade_index:
            continue

        for next_index in range(
            current_index + 1,
            max_grade_index + 1
        ):

            previous_grade = GRADE_ORDER[
                next_index - 1
            ]

            next_grade = GRADE_ORDER[
                next_index
            ]

            point_gain = (
                GRADE_POINTS[next_grade]
                - GRADE_POINTS[previous_grade]
            ) * course.gpa_credit

            upgrades.append({
                "course": course,
                "from_grade": previous_grade,
                "to_grade": next_grade,
                "point_gain": point_gain,
            })

        upgrades.sort(
            key=lambda item: (
                -item["point_gain"],
                GRADE_POINTS[item["from_grade"]],
            )
        )

    accumulated_points = 0.0
    selected_upgrades = []

    for upgrade in upgrades:

        if accumulated_points >= required_points:
            break

        selected_upgrades.append(
            upgrade
        )

        accumulated_points += (
            upgrade["point_gain"]
        )

    course_changes = {}

    for upgrade in selected_upgrades:

        course = upgrade["course"]

        if course.code not in course_changes:
            course_changes[course.code] = {
                "course_code": course.code,
                "course_name": course.name,
                "credit": course.gpa_credit,
                "old_grade": course.grade,
                "new_grade": upgrade["to_grade"],
                "point_gain": 0.0,
            }

        course_changes[
            course.code
        ]["new_grade"] = upgrade["to_grade"]

        course_changes[
            course.code
        ]["point_gain"] += upgrade["point_gain"]

    return {
        "plan": list(
            course_changes.values()
        ),
        "total_point_gain": accumulated_points,
    }


def find_target_plan(
    courses: list[Course],
    target_gpa: float,
    strategy: str = "min_courses",
    max_grade: str = "AA",
    official_cgpa: float | None = None,
) -> dict:

    if strategy not in VALID_STRATEGIES:
        raise ValueError(
            f"Invalid strategy: {strategy}"
        )

    target_analysis = analyze_target_gpa(
        courses,
        target_gpa,
        official_cgpa=official_cgpa,
    )

    if target_analysis["already_reached"]:
        return {
            "reachable": True,
            "already_reached": True,
            "strategy": strategy,
            "max_grade": max_grade,
            "plan": [],
            "projected_gpa": target_analysis["current_gpa"],
            "total_point_gain": 0.0,
        }


    if strategy == "minimal_change":

        minimal_result = find_minimal_change_plan(
            courses=courses,
            required_points=target_analysis["required_points"],
            max_grade=max_grade,
        )

        accumulated_points = minimal_result[
            "total_point_gain"
        ]

        reachable = (
            accumulated_points
            >= target_analysis["required_points"]
        )

        projected_points = (
            target_analysis["current_points"]
            + accumulated_points
        )

        projected_gpa = (
            projected_points
            / target_analysis["total_credits"]
        )

        return {
            "reachable": reachable,
            "already_reached": False,
            "strategy": strategy,
            "max_grade": max_grade,
            "plan": minimal_result["plan"],
            "projected_gpa": projected_gpa,
            "total_point_gain": accumulated_points,
            "required_point_gain": target_analysis[
                "required_points"
            ],
        }

    options = build_improvement_options(
        courses,
        max_grade
    )

    # ---------------------------------
    # Strateji 1:
    # En az sayıda ders
    #
    # En fazla puan kazandıran derslerden
    # başlayarak hedefe ulaşmaya çalışır.
    # ---------------------------------
    if strategy == "min_courses":

        options.sort(
            key=lambda item: item["point_gain"],
            reverse=True
        )

    # ---------------------------------
    # Strateji 2:
    # En düşük notlardan başla
    # ---------------------------------
    elif strategy == "lowest_grades":

        options.sort(
            key=lambda item: (
                GRADE_POINTS[item["old_grade"]],
                -item["credit"],
            )
        )

    # ---------------------------------
    # Strateji 3:
    # GPA etkisi en yüksek dersler
    # ---------------------------------
   

    required_points = target_analysis[
        "required_points"
    ]

    accumulated_points = 0.0
    plan = []

    for option in options:

        plan.append(option)

        accumulated_points += option[
            "point_gain"
        ]

        if accumulated_points >= required_points:
            break

    reachable = (
        accumulated_points >= required_points
    )

    projected_points = (
        target_analysis["current_points"]
        + accumulated_points
    )

    projected_gpa = (
        projected_points
        / target_analysis["total_credits"]
    )

    return {
        "reachable": reachable,
        "already_reached": False,
        "strategy": strategy,
        "max_grade": max_grade,
        "plan": plan,
        "projected_gpa": projected_gpa,
        "total_point_gain": accumulated_points,
        "required_point_gain": required_points,
    }