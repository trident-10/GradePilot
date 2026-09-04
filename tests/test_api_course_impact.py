from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from core.course_impact_engine import analyze_course_impact
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
    name: str = "Course",
    semester: str | None = "2024-2025 Güz",
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


SAMPLE = [
    _course(code="CENG101", name="Programming", grade="DD", gpa_credit=4),
    _course(code="MATH101", name="Mathematics", grade="AA", gpa_credit=4),
]


def test_valid_course_returns_higher_grade_options(client):
    response = client.post(
        "/api/academic/course-impact",
        json={"courses": SAMPLE, "course_code": "CENG101"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["course"]["code"] == "CENG101"
    assert body["course"]["current_grade"] == "DD"
    grades = [row["grade"] for row in body["options"]]
    assert grades == ["DC", "CC", "CB", "BB", "BA", "AA"]
    assert all(row["projected_gpa"] > body["current_gpa"] for row in body["options"])


def test_projected_gpa_matches_engine(client):
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
            grade="AA",
            semester="2024-2025 Güz",
        ),
    ]
    engine = analyze_course_impact(engine_courses, "CENG101")
    body = client.post(
        "/api/academic/course-impact",
        json={"courses": SAMPLE, "course_code": "CENG101"},
    ).json()

    assert body["options"][0]["grade"] == engine["scenarios"][0]["grade"]
    assert body["options"][-1]["projected_gpa"] == pytest.approx(
        engine["scenarios"][-1]["new_gpa"]
    )
    assert body["options"][-1]["projected_gpa"] == pytest.approx(4.0)


def test_gpa_gain_is_correct(client):
    body = client.post(
        "/api/academic/course-impact",
        json={"courses": SAMPLE, "course_code": "CENG101"},
    ).json()
    aa = next(row for row in body["options"] if row["grade"] == "AA")
    assert aa["gpa_gain"] == pytest.approx(1.5)
    assert aa["projected_gpa"] == pytest.approx(
        body["current_gpa"] + aa["gpa_gain"]
    )


def test_aa_course_returns_no_upgrades(client):
    response = client.post(
        "/api/academic/course-impact",
        json={"courses": SAMPLE, "course_code": "MATH101"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["course"]["current_grade"] == "AA"
    assert body["options"] == []


def test_missing_course_returns_400(client):
    response = client.post(
        "/api/academic/course-impact",
        json={"courses": SAMPLE, "course_code": "UNKNOWN"},
    )
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_repeat_resolution_uses_source_order(client):
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
            _course(
                code="MATH157",
                grade="AA",
                gpa_credit=4,
                semester="2024-2025 Güz",
                source_order=5,
            ),
        ],
        "course_code": "CENG111",
    }
    body = client.post("/api/academic/course-impact", json=payload).json()
    assert body["course"]["current_grade"] == "BA"
    assert [row["grade"] for row in body["options"]] == ["AA"]


def test_reordered_request_does_not_change_result(client):
    older = _course(
        code="CENG111",
        grade="DD",
        gpa_credit=4,
        source_order=4,
        semester="2024-2025 Güz",
    )
    newer = _course(
        code="CENG111",
        grade="BA",
        gpa_credit=4,
        source_order=19,
        semester="2025-2026 Güz",
    )
    other = _course(
        code="MATH157",
        grade="AA",
        gpa_credit=4,
        source_order=5,
        semester="2024-2025 Güz",
    )
    first = client.post(
        "/api/academic/course-impact",
        json={"courses": [older, newer, other], "course_code": "CENG111"},
    ).json()
    reversed_order = client.post(
        "/api/academic/course-impact",
        json={"courses": [other, newer, older], "course_code": "CENG111"},
    ).json()
    assert first["course"]["current_grade"] == reversed_order["course"]["current_grade"]
    assert first["current_gpa"] == pytest.approx(reversed_order["current_gpa"])
    assert first["options"] == reversed_order["options"]


def test_credit_weighting_works(client):
    courses = [
        _course(
            code="CENG111",
            grade="FF",
            gpa_credit=2,
            local_credit=2,
            ects=6,
        ),
        _course(
            code="MATH157",
            grade="AA",
            gpa_credit=6,
            local_credit=6,
            ects=2,
        ),
    ]
    body = client.post(
        "/api/academic/course-impact",
        json={"courses": courses, "course_code": "CENG111"},
    ).json()
    assert body["current_gpa"] == pytest.approx(3.0)
    aa = next(row for row in body["options"] if row["grade"] == "AA")
    assert aa["projected_gpa"] == pytest.approx(4.0)


def test_ects_weighting_works(client):
    courses = [
        _course(
            code="CENG111",
            grade="FF",
            gpa_credit=6,
            local_credit=2,
            ects=6,
        ),
        _course(
            code="MATH157",
            grade="AA",
            gpa_credit=2,
            local_credit=6,
            ects=2,
        ),
    ]
    body = client.post(
        "/api/academic/course-impact",
        json={"courses": courses, "course_code": "CENG111"},
    ).json()
    assert body["current_gpa"] == pytest.approx(1.0)
    aa = next(row for row in body["options"] if row["grade"] == "AA")
    assert aa["projected_gpa"] == pytest.approx(4.0)


def test_invalid_grade_rejected(client):
    response = client.post(
        "/api/academic/course-impact",
        json={
            "courses": [
                _course(code="X", grade="ZZ", gpa_credit=3),
            ],
            "course_code": "X",
        },
    )
    assert response.status_code == 400


def test_empty_courses_rejected(client):
    response = client.post(
        "/api/academic/course-impact",
        json={"courses": [], "course_code": "CENG101"},
    )
    assert response.status_code == 400


def test_semester_null_is_valid(client):
    response = client.post(
        "/api/academic/course-impact",
        json={
            "courses": [
                _course(
                    code="CENG101",
                    grade="DD",
                    gpa_credit=4,
                    semester=None,
                ),
                _course(
                    code="MATH101",
                    grade="AA",
                    gpa_credit=4,
                    semester=None,
                ),
            ],
            "course_code": "CENG101",
        },
    )
    assert response.status_code == 200
    assert response.json()["options"]


def test_engine_latest_attempts_used():
    courses = [
        Course(
            code="CENG111",
            name="Programming",
            gpa_credit=4,
            grade="DD",
            semester="A",
            source_order=1,
        ),
        Course(
            code="CENG111",
            name="Programming",
            gpa_credit=4,
            grade="BA",
            semester="B",
            source_order=2,
        ),
    ]
    active = keep_latest_attempts(courses)
    engine = analyze_course_impact(active, "CENG111")
    assert engine["current_grade"] == "BA"
