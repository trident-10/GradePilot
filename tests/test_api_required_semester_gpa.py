from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from core.required_gpa_engine import calculate_required_semester_gpa
from models.course import Course
from parsers.transcript_parser import keep_latest_attempts
from services.required_gpa_service import (
    RequiredGpaValidationError,
    build_required_semester_gpa,
)


@pytest.fixture
def client():
    return TestClient(create_app())


def _course(
    *,
    code: str,
    grade: str,
    gpa_credit: float,
    source_order: int | None = None,
    semester: str | None = "2024-2025 Güz",
    name: str = "Course",
) -> dict:
    payload = {
        "code": code,
        "name": name,
        "gpa_credit": gpa_credit,
        "grade": grade,
        "semester": semester,
    }
    if source_order is not None:
        payload["source_order"] = source_order
    return payload


SAMPLE = [_course(code="CENG101", grade="BB", gpa_credit=4, name="Programming")]


def test_reachable_target_returns_required_gpa(client):
    response = client.post(
        "/api/academic/required-semester-gpa",
        json={
            "courses": SAMPLE,
            "target_gpa": 3.5,
            "future_gpa_weight": 4,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["reachable"] is True
    assert body["already_reached"] is False
    assert body["required_semester_gpa"] == pytest.approx(4.0)
    assert body["current_gpa"] == pytest.approx(3.0)


def test_unreachable_target_is_http_200(client):
    response = client.post(
        "/api/academic/required-semester-gpa",
        json={
            "courses": SAMPLE,
            "target_gpa": 3.75,
            "future_gpa_weight": 4,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["reachable"] is False
    assert body["already_reached"] is False
    assert body["required_semester_gpa"] == pytest.approx(4.5)


def test_zero_required_future_points(client):
    response = client.post(
        "/api/academic/required-semester-gpa",
        json={
            "courses": [
                _course(code="AA101", grade="AA", gpa_credit=4, name="High")
            ],
            "target_gpa": 1.0,
            "future_gpa_weight": 4,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["already_reached"] is True
    assert body["reachable"] is True
    assert body["required_semester_gpa"] == pytest.approx(0.0)


def test_current_gpa_above_target_can_still_require_positive_semester(client):
    courses = [
        _course(code="OLD101", grade="BB", gpa_credit=72, name="Block A"),
        _course(code="OLD102", grade="BA", gpa_credit=18, name="Block B"),
    ]
    body = client.post(
        "/api/academic/required-semester-gpa",
        json={
            "courses": courses,
            "target_gpa": 3.0,
            "future_gpa_weight": 30,
        },
    ).json()
    assert body["current_gpa"] == pytest.approx(3.10)
    assert body["current_gpa"] > body["target_gpa"]
    assert body["already_reached"] is False
    assert body["reachable"] is True
    assert body["required_semester_gpa"] == pytest.approx(2.7)
    assert body["required_semester_gpa"] > 0


def test_formula_matches_existing_engine(client):
    engine_courses = [
        Course(
            code="CENG101",
            name="Programming",
            gpa_credit=4,
            grade="BB",
            semester="2024-2025 Güz",
        )
    ]
    engine = calculate_required_semester_gpa(
        courses=keep_latest_attempts(engine_courses),
        future_credits=4,
        target_cgpa=3.5,
    )
    body = client.post(
        "/api/academic/required-semester-gpa",
        json={
            "courses": SAMPLE,
            "target_gpa": 3.5,
            "future_gpa_weight": 4,
        },
    ).json()
    assert body["required_semester_gpa"] == pytest.approx(
        engine["required_semester_gpa"]
    )
    assert body["reachable"] is engine["reachable"]
    assert body["already_reached"] is engine["already_reached"]
    assert body["current_gpa"] == pytest.approx(engine["current_cgpa"])
    assert "required_future_points" not in body
    assert "current_points" not in body


def test_credit_weighting_works(client):
    body = client.post(
        "/api/academic/required-semester-gpa",
        json={
            "courses": [
                _course(code="A", grade="AA", gpa_credit=2),
                _course(code="B", grade="FF", gpa_credit=6),
            ],
            "target_gpa": 2.0,
            "future_gpa_weight": 4,
        },
    ).json()
    # current points 8, total weight 12, need 24, future points 16 → 4.0
    assert body["current_gpa"] == pytest.approx(1.0)
    assert body["required_semester_gpa"] == pytest.approx(4.0)
    assert body["reachable"] is True


def test_ects_weighting_works(client):
    body = client.post(
        "/api/academic/required-semester-gpa",
        json={
            "courses": [
                _course(code="A", grade="AA", gpa_credit=6),
                _course(code="B", grade="FF", gpa_credit=2),
            ],
            "target_gpa": 2.0,
            "future_gpa_weight": 4,
        },
    ).json()
    credit = client.post(
        "/api/academic/required-semester-gpa",
        json={
            "courses": [
                _course(code="A", grade="AA", gpa_credit=2),
                _course(code="B", grade="FF", gpa_credit=6),
            ],
            "target_gpa": 2.0,
            "future_gpa_weight": 4,
        },
    ).json()
    assert body["current_gpa"] == pytest.approx(3.0)
    assert body["current_gpa"] != credit["current_gpa"]
    assert body["required_semester_gpa"] != credit["required_semester_gpa"]


def test_empty_courses_rejected(client):
    response = client.post(
        "/api/academic/required-semester-gpa",
        json={"courses": [], "target_gpa": 3.0, "future_gpa_weight": 20},
    )
    assert response.status_code == 400


def test_target_outside_range_rejected(client):
    high = client.post(
        "/api/academic/required-semester-gpa",
        json={"courses": SAMPLE, "target_gpa": 4.01, "future_gpa_weight": 20},
    )
    low = client.post(
        "/api/academic/required-semester-gpa",
        json={"courses": SAMPLE, "target_gpa": -0.1, "future_gpa_weight": 20},
    )
    assert high.status_code == 400
    assert low.status_code == 400


def test_future_weight_not_positive_rejected(client):
    zero = client.post(
        "/api/academic/required-semester-gpa",
        json={"courses": SAMPLE, "target_gpa": 3.0, "future_gpa_weight": 0},
    )
    negative = client.post(
        "/api/academic/required-semester-gpa",
        json={"courses": SAMPLE, "target_gpa": 3.0, "future_gpa_weight": -5},
    )
    assert zero.status_code == 400
    assert negative.status_code == 400


def test_nan_and_infinite_values_rejected():
    courses = [
        Course(
            code="CENG101",
            name="Programming",
            gpa_credit=4,
            grade="BB",
            semester="2024-2025 Güz",
        )
    ]
    with pytest.raises(RequiredGpaValidationError):
        build_required_semester_gpa(courses, float("nan"), 20)
    with pytest.raises(RequiredGpaValidationError):
        build_required_semester_gpa(courses, 3.0, float("inf"))


def test_repeat_resolution_uses_source_order(client):
    body = client.post(
        "/api/academic/required-semester-gpa",
        json={
            "courses": [
                _course(
                    code="CENG111",
                    grade="DD",
                    gpa_credit=4,
                    source_order=4,
                ),
                _course(
                    code="CENG111",
                    grade="BA",
                    gpa_credit=4,
                    source_order=19,
                ),
            ],
            "target_gpa": 3.75,
            "future_gpa_weight": 4,
        },
    ).json()
    # active BA 3.5 * 4 = 14; need 3.75*8=30; future 16 → 4.0
    assert body["current_gpa"] == pytest.approx(3.5)
    assert body["required_semester_gpa"] == pytest.approx(4.0)


def test_reordering_does_not_change_result(client):
    older = _course(code="CENG111", grade="DD", gpa_credit=4, source_order=1)
    newer = _course(code="CENG111", grade="BA", gpa_credit=4, source_order=2)
    other = _course(code="MATH157", grade="CC", gpa_credit=4, source_order=3)
    payload = {
        "target_gpa": 3.0,
        "future_gpa_weight": 8,
    }
    first = client.post(
        "/api/academic/required-semester-gpa",
        json={"courses": [older, newer, other], **payload},
    ).json()
    reversed_order = client.post(
        "/api/academic/required-semester-gpa",
        json={"courses": [other, newer, older], **payload},
    ).json()
    assert first["current_gpa"] == pytest.approx(reversed_order["current_gpa"])
    assert first["required_semester_gpa"] == pytest.approx(
        reversed_order["required_semester_gpa"]
    )
    assert first["reachable"] == reversed_order["reachable"]
