from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from core.target_engine import find_target_plan
from models.course import Course
from parsers.transcript_parser import keep_latest_attempts


@pytest.fixture
def client():
    return TestClient(create_app())


def _course(
    *,
    code: str,
    grade: str,
    gpa_credit: float,
    semester: str | None = "2024-2025 Güz",
    name: str = "Course",
    source_order: int | None = None,
    ects: float | None = None,
    local_credit: float | None = None,
) -> dict:
    payload = {
        "code": code,
        "name": name,
        "gpa_credit": gpa_credit,
        "grade": grade,
        "semester": semester,
        "ects": ects,
        "local_credit": local_credit,
    }
    if source_order is not None:
        payload["source_order"] = source_order
    return payload


def _body(courses: list[dict], **overrides):
    payload = {
        "courses": courses,
        "target_gpa": 2.0,
        "max_grade": "BB",
        "strategy": "min_courses",
    }
    payload.update(overrides)
    return payload


SAMPLE_COURSES = [
    _course(code="CENG101", grade="DD", gpa_credit=4, name="Programming"),
    _course(code="MATH101", grade="CC", gpa_credit=4, name="Mathematics"),
]


def test_reachable_target_returns_plan(client):
    response = client.post(
        "/api/academic/target-plan",
        json=_body(SAMPLE_COURSES, target_gpa=2.0, max_grade="BB"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["reachable"] is True
    assert body["already_reached"] is False
    assert body["estimated_gpa"] >= 2.0
    assert len(body["changes"]) > 0
    assert "point_gain" not in str(body)
    assert "relative_position" not in str(body)


def test_unreachable_target_is_not_http_error(client):
    response = client.post(
        "/api/academic/target-plan",
        json=_body(
            SAMPLE_COURSES,
            target_gpa=4.0,
            max_grade="CC",
            strategy="min_courses",
        ),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["reachable"] is False
    assert body["already_reached"] is False
    assert body["estimated_gpa"] < 4.0
    assert body["maximum_possible_gpa"] == pytest.approx(body["estimated_gpa"])


def test_already_reached_target(client):
    response = client.post(
        "/api/academic/target-plan",
        json=_body(SAMPLE_COURSES, target_gpa=1.0, max_grade="AA"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["already_reached"] is True
    assert body["reachable"] is True
    assert body["changes"] == []
    assert body["estimated_gpa"] == pytest.approx(body["current_gpa"])


def test_min_courses_strategy(client):
    body = client.post(
        "/api/academic/target-plan",
        json=_body(SAMPLE_COURSES, strategy="min_courses", max_grade="AA"),
    ).json()
    assert body["strategy"] == "min_courses"
    assert body["reachable"] is True


def test_lowest_grades_strategy(client):
    body = client.post(
        "/api/academic/target-plan",
        json=_body(
            SAMPLE_COURSES,
            strategy="lowest_grades",
            max_grade="AA",
            target_gpa=2.0,
        ),
    ).json()
    assert body["strategy"] == "lowest_grades"
    assert body["reachable"] is True
    assert body["changes"][0]["from_grade"] == "DD"


def test_minimal_change_strategy(client):
    body = client.post(
        "/api/academic/target-plan",
        json=_body(
            SAMPLE_COURSES,
            strategy="minimal_change",
            max_grade="AA",
            target_gpa=2.0,
        ),
    ).json()
    assert body["strategy"] == "minimal_change"
    assert body["reachable"] is True
    assert len(body["changes"]) > 0


def test_invalid_strategy_rejected(client):
    response = client.post(
        "/api/academic/target-plan",
        json=_body(SAMPLE_COURSES, strategy="random_strategy"),
    )
    assert response.status_code == 400
    assert "strategy" in response.json()["detail"].lower()


def test_invalid_max_grade_rejected(client):
    response = client.post(
        "/api/academic/target-plan",
        json=_body(SAMPLE_COURSES, max_grade="ZZ"),
    )
    assert response.status_code == 400
    assert "grade" in response.json()["detail"].lower()


def test_target_gpa_outside_range_rejected(client):
    too_high = client.post(
        "/api/academic/target-plan",
        json=_body(SAMPLE_COURSES, target_gpa=4.01),
    )
    too_low = client.post(
        "/api/academic/target-plan",
        json=_body(SAMPLE_COURSES, target_gpa=-0.1),
    )
    assert too_high.status_code == 400
    assert too_low.status_code == 400
    assert "0.00" in too_high.json()["detail"]


def test_reordered_repeat_courses_do_not_change_plan(client):
    older = _course(
        code="CENG111",
        grade="DD",
        gpa_credit=4,
        semester="2024-2025 Güz",
        source_order=4,
        name="Programming I",
    )
    newer = _course(
        code="CENG111",
        grade="BA",
        gpa_credit=4,
        semester="2025-2026 Güz",
        source_order=19,
        name="Programming I",
    )
    other = _course(
        code="MATH157",
        grade="DD",
        gpa_credit=4,
        semester="2024-2025 Güz",
        source_order=5,
        name="Math",
    )

    first = client.post(
        "/api/academic/target-plan",
        json=_body(
            [older, newer, other],
            target_gpa=3.0,
            max_grade="AA",
            strategy="min_courses",
        ),
    ).json()
    reversed_order = client.post(
        "/api/academic/target-plan",
        json=_body(
            [other, newer, older],
            target_gpa=3.0,
            max_grade="AA",
            strategy="min_courses",
        ),
    ).json()

    assert first["current_gpa"] == pytest.approx(reversed_order["current_gpa"])
    assert first["estimated_gpa"] == pytest.approx(
        reversed_order["estimated_gpa"]
    )
    assert first["reachable"] == reversed_order["reachable"]
    first_codes = [(row["code"], row["from_grade"], row["to_grade"]) for row in first["changes"]]
    reversed_codes = [
        (row["code"], row["from_grade"], row["to_grade"])
        for row in reversed_order["changes"]
    ]
    assert first_codes == reversed_codes
    assert all(row["from_grade"] != "DD" or row["code"] != "CENG111" for row in first["changes"])


def test_credit_weighting_plan(client):
    courses = [
        _course(
            code="CENG111",
            grade="AA",
            gpa_credit=2,
            local_credit=2,
            ects=6,
        ),
        _course(
            code="MATH157",
            grade="FF",
            gpa_credit=6,
            local_credit=6,
            ects=2,
        ),
    ]
    body = client.post(
        "/api/academic/target-plan",
        json=_body(courses, target_gpa=2.0, max_grade="AA"),
    ).json()
    assert body["current_gpa"] == pytest.approx(1.0)
    assert body["reachable"] is True


def test_ects_weighting_plan(client):
    courses = [
        _course(
            code="CENG111",
            grade="AA",
            gpa_credit=6,
            local_credit=2,
            ects=6,
        ),
        _course(
            code="MATH157",
            grade="FF",
            gpa_credit=2,
            local_credit=6,
            ects=2,
        ),
    ]
    body = client.post(
        "/api/academic/target-plan",
        json=_body(courses, target_gpa=3.5, max_grade="AA"),
    ).json()
    assert body["current_gpa"] == pytest.approx(3.0)
    credit_body = client.post(
        "/api/academic/target-plan",
        json=_body(
            [
                _course(
                    code="CENG111",
                    grade="AA",
                    gpa_credit=2,
                    local_credit=2,
                    ects=6,
                ),
                _course(
                    code="MATH157",
                    grade="FF",
                    gpa_credit=6,
                    local_credit=6,
                    ects=2,
                ),
            ],
            target_gpa=3.5,
            max_grade="AA",
        ),
    ).json()
    assert body["current_gpa"] != credit_body["current_gpa"]


def test_planner_matches_existing_target_engine(client):
    engine_courses = [
        Course(
            code="CENG101",
            name="Programming",
            gpa_credit=4,
            grade="DD",
            semester="2024-2025 Güz",
        ),
        Course(
            code="MATH101",
            name="Mathematics",
            gpa_credit=4,
            grade="CC",
            semester="2024-2025 Güz",
        ),
    ]
    engine = find_target_plan(
        courses=keep_latest_attempts(engine_courses),
        target_gpa=2.0,
        strategy="min_courses",
        max_grade="BB",
    )
    body = client.post(
        "/api/academic/target-plan",
        json=_body(SAMPLE_COURSES, target_gpa=2.0, max_grade="BB"),
    ).json()

    assert body["reachable"] is engine["reachable"]
    assert body["already_reached"] is engine["already_reached"]
    assert body["estimated_gpa"] == pytest.approx(engine["projected_gpa"])
    assert len(body["changes"]) == len(engine["plan"])
    assert body["changes"][0]["code"] == engine["plan"][0]["course_code"]
    assert body["changes"][0]["from_grade"] == engine["plan"][0]["old_grade"]
    assert body["changes"][0]["to_grade"] == engine["plan"][0]["new_grade"]
    assert body["changes"][0]["gpa_gain"] is not None


def test_empty_courses_rejected(client):
    response = client.post(
        "/api/academic/target-plan",
        json=_body([], target_gpa=3.0),
    )
    assert response.status_code == 400
