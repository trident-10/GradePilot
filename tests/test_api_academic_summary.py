from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from core.gpa_engine import calculate_gpa
from models.course import Course
from parsers.transcript_parser import keep_latest_attempts
from services.academic_summary_service import build_academic_summary


@pytest.fixture
def client():
    return TestClient(create_app())


def _course(
    *,
    code: str,
    grade: str,
    gpa_credit: float,
    semester: str | None = None,
    ects: float | None = None,
    local_credit: float | None = None,
    source_order: int | None = None,
    name: str = "Course",
) -> dict:
    payload = {
        "code": code,
        "name": name,
        "gpa_credit": gpa_credit,
        "ects": ects,
        "local_credit": local_credit,
        "grade": grade,
        "semester": semester,
    }
    if source_order is not None:
        payload["source_order"] = source_order
    return payload


def test_summary_uses_existing_gpa_engine(client):
    payload = {
        "courses": [
            _course(code="A", grade="AA", gpa_credit=4, semester="2024 Güz"),
            _course(code="B", grade="BB", gpa_credit=4, semester="2024 Güz"),
        ]
    }

    response = client.post("/api/academic/summary", json=payload)
    assert response.status_code == 200
    body = response.json()

    expected = calculate_gpa(
        [
            Course(
                code="A",
                name="Course",
                gpa_credit=4,
                grade="AA",
                semester="2024 Güz",
            ),
            Course(
                code="B",
                name="Course",
                gpa_credit=4,
                grade="BB",
                semester="2024 Güz",
            ),
        ]
    )

    assert body["current_gpa"] == pytest.approx(expected)
    assert body["total_gpa_weight"] == pytest.approx(8.0)
    assert body["active_course_count"] == 2
    assert "path" not in body
    assert "relative_position" not in str(body)
    assert "source_order" not in body


def test_credit_weighting_produces_expected_result(client):
    payload = {
        "courses": [
            _course(
                code="CENG111",
                grade="DD",
                gpa_credit=4,
                local_credit=4,
                ects=6,
                semester="2024-2025 Güz",
            ),
            _course(
                code="MATH157",
                grade="BB",
                gpa_credit=4,
                local_credit=4,
                ects=6,
                semester="2024-2025 Güz",
            ),
        ]
    }

    response = client.post("/api/academic/summary", json=payload)
    body = response.json()

    # DD(1)*4 + BB(3)*4 = 16 / 8 = 2.0
    assert body["current_gpa"] == pytest.approx(2.0)
    assert body["total_gpa_weight"] == pytest.approx(8.0)


def test_ects_weighting_produces_expected_result(client):
    # Unequal local/ECTS ratios so weighting mode changes GANO.
    payload = {
        "courses": [
            _course(
                code="CENG111",
                grade="AA",
                gpa_credit=6,
                local_credit=2,
                ects=6,
                semester="2024-2025 Güz",
            ),
            _course(
                code="MATH157",
                grade="FF",
                gpa_credit=2,
                local_credit=6,
                ects=2,
                semester="2024-2025 Güz",
            ),
        ]
    }

    response = client.post("/api/academic/summary", json=payload)
    body = response.json()

    # ECTS weights: AA(4)*6 + FF(0)*2 = 24 / 8 = 3.0
    assert body["current_gpa"] == pytest.approx(3.0)
    assert body["total_gpa_weight"] == pytest.approx(8.0)


def test_credit_and_ects_weighting_differ_when_ratios_differ(client):
    credit_payload = {
        "courses": [
            _course(
                code="CENG111",
                grade="AA",
                gpa_credit=2,
                local_credit=2,
                ects=6,
                semester="2024-2025 Güz",
            ),
            _course(
                code="MATH157",
                grade="FF",
                gpa_credit=6,
                local_credit=6,
                ects=2,
                semester="2024-2025 Güz",
            ),
        ]
    }
    ects_payload = {
        "courses": [
            _course(
                code="CENG111",
                grade="AA",
                gpa_credit=6,
                local_credit=2,
                ects=6,
                semester="2024-2025 Güz",
            ),
            _course(
                code="MATH157",
                grade="FF",
                gpa_credit=2,
                local_credit=6,
                ects=2,
                semester="2024-2025 Güz",
            ),
        ]
    }

    credit = client.post("/api/academic/summary", json=credit_payload).json()
    ects = client.post("/api/academic/summary", json=ects_payload).json()

    # Credit: 8/8 = 1.0 ; ECTS: 24/8 = 3.0
    assert credit["current_gpa"] == pytest.approx(1.0)
    assert ects["current_gpa"] == pytest.approx(3.0)
    assert credit["current_gpa"] != ects["current_gpa"]


def test_repeated_course_cumulative_uses_latest_attempt(client):
    payload = {
        "courses": [
            _course(
                code="CENG111",
                grade="DD",
                gpa_credit=4,
                semester="2024-2025 Güz",
                source_order=4,
            ),
            _course(
                code="CENG111",
                grade="BA",
                gpa_credit=4,
                semester="2025-2026 Güz",
                source_order=19,
            ),
        ]
    }

    response = client.post("/api/academic/summary", json=payload)
    body = response.json()

    latest_only = keep_latest_attempts(
        [
            Course(
                code="CENG111",
                name="Course",
                gpa_credit=4,
                grade="DD",
                semester="2024-2025 Güz",
                source_order=4,
            ),
            Course(
                code="CENG111",
                name="Course",
                gpa_credit=4,
                grade="BA",
                semester="2025-2026 Güz",
                source_order=19,
            ),
        ]
    )
    assert body["current_gpa"] == pytest.approx(calculate_gpa(latest_only))
    assert body["active_course_count"] == 1
    assert body["current_gpa"] == pytest.approx(3.5)


def test_reversed_request_order_does_not_change_cumulative_gpa(client):
    older = _course(
        code="CENG111",
        grade="DD",
        gpa_credit=4,
        semester="2024-2025 Güz",
        source_order=4,
    )
    newer = _course(
        code="CENG111",
        grade="BA",
        gpa_credit=4,
        semester="2025-2026 Güz",
        source_order=19,
    )

    chronological = client.post(
        "/api/academic/summary",
        json={"courses": [older, newer]},
    ).json()
    reversed_order = client.post(
        "/api/academic/summary",
        json={"courses": [newer, older]},
    ).json()

    assert chronological["current_gpa"] == pytest.approx(3.5)
    assert reversed_order["current_gpa"] == pytest.approx(
        chronological["current_gpa"]
    )
    assert chronological["active_course_count"] == 1
    assert reversed_order["active_course_count"] == 1
    assert {row["semester"] for row in chronological["semesters"]} == {
        "2024-2025 Güz",
        "2025-2026 Güz",
    }
    assert {row["semester"] for row in reversed_order["semesters"]} == {
        "2024-2025 Güz",
        "2025-2026 Güz",
    }


def test_source_order_selects_active_attempt_not_array_position(client):
    # Later JSON item is the older transcript attempt.
    payload = {
        "courses": [
            _course(
                code="CENG111",
                grade="BA",
                gpa_credit=4,
                semester="2025-2026 Güz",
                source_order=19,
            ),
            _course(
                code="CENG111",
                grade="DD",
                gpa_credit=4,
                semester="2024-2025 Güz",
                source_order=4,
            ),
        ]
    }

    body = client.post("/api/academic/summary", json=payload).json()
    assert body["current_gpa"] == pytest.approx(3.5)
    assert body["active_course_count"] == 1


def test_historical_semester_gpa_retains_original_attempt(client):
    payload = {
        "courses": [
            _course(
                code="CENG111",
                grade="DD",
                gpa_credit=4,
                semester="2024-2025 Güz",
                source_order=4,
            ),
            _course(
                code="CENG111",
                grade="BA",
                gpa_credit=4,
                semester="2025-2026 Güz",
                source_order=19,
            ),
        ]
    }

    response = client.post("/api/academic/summary", json=payload)
    body = response.json()
    semesters = {
        row["semester"]: row for row in body["semesters"]
    }

    assert semesters["2024-2025 Güz"]["gpa"] == pytest.approx(1.0)
    assert semesters["2024-2025 Güz"]["course_count"] == 1
    assert semesters["2025-2026 Güz"]["gpa"] == pytest.approx(3.5)
    assert semesters["2025-2026 Güz"]["course_count"] == 1


def test_missing_course_code_rejected(client):
    response = client.post(
        "/api/academic/summary",
        json={
            "courses": [
                {
                    "code": "   ",
                    "name": "Course",
                    "gpa_credit": 3,
                    "grade": "AA",
                    "semester": "2024 Güz",
                }
            ]
        },
    )
    assert response.status_code == 400
    assert "code" in response.json()["detail"].lower()


def test_invalid_grade_rejected(client):
    response = client.post(
        "/api/academic/summary",
        json={
            "courses": [
                _course(
                    code="X",
                    grade="ZZ",
                    gpa_credit=3,
                    semester="2024 Güz",
                )
            ]
        },
    )
    assert response.status_code == 400
    assert "unknown grade" in response.json()["detail"].lower()


def test_empty_course_list_rejected(client):
    response = client.post("/api/academic/summary", json={"courses": []})
    assert response.status_code == 400
    assert response.json()["detail"] == "No courses were provided."
    assert "traceback" not in str(response.json()).lower()


def test_semester_none_does_not_create_semester_row(client):
    response = client.post(
        "/api/academic/summary",
        json={
            "courses": [
                _course(
                    code="CENG111",
                    grade="AA",
                    gpa_credit=4,
                    semester=None,
                    source_order=0,
                )
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["current_gpa"] == pytest.approx(4.0)
    assert body["semesters"] == []


def test_negative_weight_rejected(client):
    response = client.post(
        "/api/academic/summary",
        json={
            "courses": [
                _course(
                    code="X",
                    grade="AA",
                    gpa_credit=-1,
                    semester="2024 Güz",
                )
            ]
        },
    )
    assert response.status_code == 400


def test_service_matches_engine_for_mixed_weights():
    courses = [
        Course(
            code="A",
            name="A",
            gpa_credit=3,
            grade="AA",
            semester="S1",
        ),
        Course(
            code="B",
            name="B",
            gpa_credit=5,
            grade="CC",
            semester="S1",
        ),
    ]
    summary = build_academic_summary(courses)
    assert summary.current_gpa == pytest.approx(calculate_gpa(courses))
    assert summary.total_gpa_weight == pytest.approx(8.0)
