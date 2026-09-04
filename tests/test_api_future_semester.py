from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from core.future_semester_engine import calculate_projected_cgpa
from models.course import Course
from parsers.transcript_parser import keep_latest_attempts


@pytest.fixture
def client():
    return TestClient(create_app())


def _current(
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


def _future(*, name: str, gpa_credit: float, grade: str, code: str | None = None):
    payload = {
        "name": name,
        "gpa_credit": gpa_credit,
        "grade": grade,
    }
    if code is not None:
        payload["code"] = code
    return payload


CURRENT = [
    _current(code="OLD101", grade="BB", gpa_credit=4, name="Current Course"),
]
FUTURE = [
    _future(name="Future Course", code="NEW101", gpa_credit=4, grade="AA"),
]


def test_valid_future_semester_returns_projected_cgpa(client):
    response = client.post(
        "/api/academic/future-semester",
        json={"courses": CURRENT, "future_courses": FUTURE},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["projected_cgpa"] == pytest.approx(3.5)
    assert body["future_semester_gpa"] == pytest.approx(4.0)
    assert body["current_gpa"] == pytest.approx(3.0)
    assert "current_points" not in body
    assert "total_points" not in body


def test_future_semester_gpa_matches_engine(client):
    engine_current = [
        Course(
            code="OLD101",
            name="Current Course",
            gpa_credit=4,
            grade="BB",
            semester="2024-2025 Güz",
        )
    ]
    engine_future = [
        Course(
            code="NEW101",
            name="Future Course",
            gpa_credit=4,
            grade="AA",
            semester="Future",
        )
    ]
    engine = calculate_projected_cgpa(engine_current, engine_future)
    body = client.post(
        "/api/academic/future-semester",
        json={"courses": CURRENT, "future_courses": FUTURE},
    ).json()
    assert body["future_semester_gpa"] == pytest.approx(engine["semester_gpa"])


def test_projected_cgpa_matches_engine(client):
    engine = calculate_projected_cgpa(
        [
            Course(
                code="OLD101",
                name="Current Course",
                gpa_credit=4,
                grade="BB",
                semester="2024-2025 Güz",
            )
        ],
        [
            Course(
                code="NEW101",
                name="Future Course",
                gpa_credit=4,
                grade="AA",
                semester="Future",
            )
        ],
    )
    body = client.post(
        "/api/academic/future-semester",
        json={"courses": CURRENT, "future_courses": FUTURE},
    ).json()
    assert body["projected_cgpa"] == pytest.approx(engine["projected_cgpa"])
    assert body["current_gpa_weight"] == pytest.approx(engine["current_credits"])
    assert body["future_gpa_weight"] == pytest.approx(engine["future_credits"])
    assert body["projected_total_weight"] == pytest.approx(engine["total_credits"])


def test_credit_weighting_works(client):
    current = [
        _current(code="A", grade="AA", gpa_credit=2),
        _current(code="B", grade="FF", gpa_credit=6),
    ]
    future = [_future(name="NEW", gpa_credit=2, grade="AA")]
    body = client.post(
        "/api/academic/future-semester",
        json={"courses": current, "future_courses": future},
    ).json()
    # current 8/8 = 1.0; plus 8 future points / 2 credits → 16/10 = 1.6
    assert body["current_gpa"] == pytest.approx(1.0)
    assert body["projected_cgpa"] == pytest.approx(1.6)


def test_ects_weighting_works(client):
    current = [
        _current(code="A", grade="AA", gpa_credit=6),
        _current(code="B", grade="FF", gpa_credit=2),
    ]
    future = [_future(name="NEW", gpa_credit=6, grade="AA")]
    body = client.post(
        "/api/academic/future-semester",
        json={"courses": current, "future_courses": future},
    ).json()
    assert body["current_gpa"] == pytest.approx(3.0)
    credit_body = client.post(
        "/api/academic/future-semester",
        json={
            "courses": [
                _current(code="A", grade="AA", gpa_credit=2),
                _current(code="B", grade="FF", gpa_credit=6),
            ],
            "future_courses": [_future(name="NEW", gpa_credit=2, grade="AA")],
        },
    ).json()
    assert body["current_gpa"] != credit_body["current_gpa"]
    assert body["projected_cgpa"] != credit_body["projected_cgpa"]


def test_empty_future_course_list_rejected(client):
    response = client.post(
        "/api/academic/future-semester",
        json={"courses": CURRENT, "future_courses": []},
    )
    assert response.status_code == 400
    assert "future course" in response.json()["detail"].lower()


def test_invalid_grade_rejected(client):
    response = client.post(
        "/api/academic/future-semester",
        json={
            "courses": CURRENT,
            "future_courses": [_future(name="NEW", gpa_credit=3, grade="ZZ")],
        },
    )
    assert response.status_code == 400


def test_zero_and_negative_future_weight_rejected(client):
    zero = client.post(
        "/api/academic/future-semester",
        json={
            "courses": CURRENT,
            "future_courses": [_future(name="NEW", gpa_credit=0, grade="AA")],
        },
    )
    negative = client.post(
        "/api/academic/future-semester",
        json={
            "courses": CURRENT,
            "future_courses": [_future(name="NEW", gpa_credit=-1, grade="AA")],
        },
    )
    assert zero.status_code == 400
    assert negative.status_code == 400


def test_repeat_resolution_remains_stable(client):
    payload = {
        "courses": [
            _current(
                code="CENG111",
                grade="DD",
                gpa_credit=4,
                source_order=4,
                semester="2024-2025 Güz",
            ),
            _current(
                code="CENG111",
                grade="BA",
                gpa_credit=4,
                source_order=19,
                semester="2025-2026 Güz",
            ),
        ],
        "future_courses": [_future(name="NEW101", gpa_credit=4, grade="AA")],
    }
    body = client.post("/api/academic/future-semester", json=payload).json()
    assert body["current_gpa"] == pytest.approx(3.5)
    assert body["current_gpa_weight"] == pytest.approx(4.0)


def test_reordered_current_courses_do_not_change_gpa(client):
    older = _current(code="CENG111", grade="DD", gpa_credit=4, source_order=1)
    newer = _current(code="CENG111", grade="BA", gpa_credit=4, source_order=2)
    other = _current(code="MATH157", grade="CC", gpa_credit=4, source_order=3)
    future = [_future(name="NEW", gpa_credit=3, grade="BB")]
    first = client.post(
        "/api/academic/future-semester",
        json={"courses": [older, newer, other], "future_courses": future},
    ).json()
    reversed_order = client.post(
        "/api/academic/future-semester",
        json={"courses": [other, newer, older], "future_courses": future},
    ).json()
    assert first["current_gpa"] == pytest.approx(reversed_order["current_gpa"])
    assert first["projected_cgpa"] == pytest.approx(
        reversed_order["projected_cgpa"]
    )


def test_duplicate_code_is_additional_coursework_not_retake(client):
    """Engine has no retake replacement; matching codes are added, not swapped."""
    current = [_current(code="CENG111", grade="DD", gpa_credit=4)]
    future = [_future(name="CENG111", code="CENG111", gpa_credit=4, grade="AA")]
    body = client.post(
        "/api/academic/future-semester",
        json={"courses": current, "future_courses": future},
    ).json()
    engine = calculate_projected_cgpa(
        keep_latest_attempts(
            [
                Course(
                    code="CENG111",
                    name="Course",
                    gpa_credit=4,
                    grade="DD",
                    semester="2024-2025 Güz",
                )
            ]
        ),
        [
            Course(
                code="CENG111",
                name="CENG111",
                gpa_credit=4,
                grade="AA",
                semester="Future",
            )
        ],
    )
    assert body["projected_total_weight"] == pytest.approx(8.0)
    assert body["projected_cgpa"] == pytest.approx(engine["projected_cgpa"])
    assert body["projected_cgpa"] == pytest.approx(2.5)


def test_empty_current_courses_rejected(client):
    response = client.post(
        "/api/academic/future-semester",
        json={"courses": [], "future_courses": FUTURE},
    )
    assert response.status_code == 400


def test_omitted_future_code_is_not_copied_from_name():
    from services.future_semester_service import validate_and_build_future_courses

    courses = validate_and_build_future_courses(
        [
            {
                "name": "SENG301",
                "gpa_credit": 3,
                "grade": "BA",
            }
        ]
    )
    assert courses[0].name == "SENG301"
    assert courses[0].code == ""
