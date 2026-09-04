from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from core.scenario_engine import simulate_multiple_grade_changes
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
    source_order: int | None = None,
    ects: float | None = None,
    local_credit: float | None = None,
) -> dict:
    item = {
        "code": code,
        "name": name,
        "gpa_credit": gpa_credit,
        "grade": grade,
        "semester": "2025-2026 Güz",
        "ects": ects,
        "local_credit": local_credit,
    }
    if source_order is not None:
        item["source_order"] = source_order
    return item


SAMPLE = [
    _course(
        code="CENG218",
        name="Data Structures",
        grade="DD",
        gpa_credit=4,
        source_order=1,
    ),
    _course(
        code="MATH205",
        name="Linear Algebra",
        grade="BB",
        gpa_credit=4,
        source_order=2,
    ),
]


def _post(client, courses, changes):
    return client.post(
        "/api/academic/manual-scenario",
        json={"courses": courses, "changes": changes},
    )


def test_one_course_scenario(client):
    response = _post(
        client,
        SAMPLE,
        [{"course_code": "CENG218", "new_grade": "BA"}],
    )
    assert response.status_code == 200
    body = response.json()
    assert body["current_gpa"] == pytest.approx(2.0)
    assert body["projected_gpa"] == pytest.approx(3.25)
    assert body["gpa_change"] == pytest.approx(1.25)
    assert body["changes"] == [
        {
            "code": "CENG218",
            "name": "Data Structures",
            "from_grade": "DD",
            "to_grade": "BA",
        }
    ]


def test_multi_course_scenario(client):
    body = _post(
        client,
        SAMPLE,
        [
            {"course_code": "CENG218", "new_grade": "AA"},
            {"course_code": "MATH205", "new_grade": "BA"},
        ],
    ).json()
    assert body["projected_gpa"] == pytest.approx(3.75)
    assert len(body["changes"]) == 2


def test_projected_gpa_and_difference_match_scenario_engine(client):
    model_courses = [
        Course(
            code=item["code"],
            name=item["name"],
            gpa_credit=item["gpa_credit"],
            grade=item["grade"],
            semester=item["semester"],
            source_order=item["source_order"],
        )
        for item in SAMPLE
    ]
    expected = simulate_multiple_grade_changes(
        model_courses,
        {"CENG218": "BA", "MATH205": "AA"},
    )
    body = _post(
        client,
        SAMPLE,
        [
            {"course_code": "CENG218", "new_grade": "BA"},
            {"course_code": "MATH205", "new_grade": "AA"},
        ],
    ).json()
    assert body["current_gpa"] == pytest.approx(expected["current_gpa"])
    assert body["projected_gpa"] == pytest.approx(expected["new_gpa"])
    assert body["gpa_change"] == pytest.approx(expected["difference"])
    assert body["projected_gpa"] - body["current_gpa"] == pytest.approx(
        body["gpa_change"]
    )


def test_repeat_uses_latest_source_order_and_historical_is_not_selected(client):
    courses = [
        _course(
            code="CENG218",
            name="Old Data Structures",
            grade="FF",
            gpa_credit=4,
            source_order=2,
        ),
        _course(
            code="MATH205",
            name="Linear Algebra",
            grade="AA",
            gpa_credit=4,
            source_order=5,
        ),
        _course(
            code="CENG218",
            name="Current Data Structures",
            grade="BB",
            gpa_credit=4,
            source_order=20,
        ),
    ]
    body = _post(
        client,
        courses,
        [{"course_code": "CENG218", "new_grade": "BA"}],
    ).json()
    assert body["current_gpa"] == pytest.approx(3.5)
    assert body["changes"][0]["name"] == "Current Data Structures"
    assert body["changes"][0]["from_grade"] == "BB"


def test_reordered_courses_give_same_result(client):
    courses = [
        _course(
            code="CENG218",
            grade="DD",
            gpa_credit=4,
            source_order=2,
        ),
        _course(
            code="CENG218",
            grade="BB",
            gpa_credit=4,
            source_order=20,
        ),
        _course(
            code="MATH205",
            grade="AA",
            gpa_credit=4,
            source_order=5,
        ),
    ]
    changes = [{"course_code": "CENG218", "new_grade": "BA"}]
    first = _post(client, courses, changes).json()
    reordered = _post(client, list(reversed(courses)), changes).json()
    assert first == reordered


@pytest.mark.parametrize(
    ("changes", "detail"),
    [
        ([], "at least one"),
        (
            [{"course_code": "UNKNOWN", "new_grade": "AA"}],
            "not found",
        ),
        (
            [{"course_code": "CENG218", "new_grade": "ZZ"}],
            "invalid grade",
        ),
        (
            [
                {"course_code": "CENG218", "new_grade": "BA"},
                {"course_code": "CENG218", "new_grade": "AA"},
            ],
            "duplicate",
        ),
        (
            [{"course_code": "CENG218", "new_grade": "DD"}],
            "must be higher",
        ),
        (
            [{"course_code": "CENG218", "new_grade": "FF"}],
            "must be higher",
        ),
    ],
)
def test_invalid_change_requests_are_rejected(client, changes, detail):
    response = _post(client, SAMPLE, changes)
    assert response.status_code == 400
    assert detail in response.json()["detail"].lower()


def test_empty_courses_are_rejected(client):
    response = _post(
        client,
        [],
        [{"course_code": "CENG218", "new_grade": "AA"}],
    )
    assert response.status_code == 400


def test_aa_course_has_no_higher_grade(client):
    courses = [
        _course(code="TOP", grade="AA", gpa_credit=3, source_order=1)
    ]
    response = _post(
        client,
        courses,
        [{"course_code": "TOP", "new_grade": "AA"}],
    )
    assert response.status_code == 400
    assert "must be higher" in response.json()["detail"].lower()


@pytest.mark.parametrize("weight", [0, -1])
def test_non_positive_gpa_weight_is_rejected(client, weight):
    courses = [
        _course(
            code="CENG218",
            grade="DD",
            gpa_credit=weight,
            source_order=1,
        )
    ]
    response = _post(
        client,
        courses,
        [{"course_code": "CENG218", "new_grade": "AA"}],
    )
    assert response.status_code == 400
    assert "gpa weight" in response.json()["detail"].lower()


def test_malformed_change_is_rejected_by_schema(client):
    response = client.post(
        "/api/academic/manual-scenario",
        json={
            "courses": SAMPLE,
            "changes": [{"course_code": "CENG218", "unexpected": "AA"}],
        },
    )
    assert response.status_code == 422


def test_credit_weighting(client):
    courses = [
        _course(
            code="LOW",
            grade="FF",
            gpa_credit=2,
            local_credit=2,
            ects=6,
            source_order=1,
        ),
        _course(
            code="HIGH",
            grade="AA",
            gpa_credit=6,
            local_credit=6,
            ects=2,
            source_order=2,
        ),
    ]
    body = _post(
        client,
        courses,
        [{"course_code": "LOW", "new_grade": "AA"}],
    ).json()
    assert body["current_gpa"] == pytest.approx(3.0)
    assert body["projected_gpa"] == pytest.approx(4.0)


def test_ects_weighting(client):
    courses = [
        _course(
            code="LOW",
            grade="FF",
            gpa_credit=6,
            local_credit=2,
            ects=6,
            source_order=1,
        ),
        _course(
            code="HIGH",
            grade="AA",
            gpa_credit=2,
            local_credit=6,
            ects=2,
            source_order=2,
        ),
    ]
    body = _post(
        client,
        courses,
        [{"course_code": "LOW", "new_grade": "AA"}],
    ).json()
    assert body["current_gpa"] == pytest.approx(1.0)
    assert body["projected_gpa"] == pytest.approx(4.0)


def test_service_uses_active_courses_before_engine():
    courses = [
        Course("X", "Old", 4, "FF", source_order=1),
        Course("X", "Current", 4, "BB", source_order=2),
    ]
    active = keep_latest_attempts(courses)
    expected = simulate_multiple_grade_changes(active, {"X": "AA"})
    assert expected["current_gpa"] == pytest.approx(3.0)
