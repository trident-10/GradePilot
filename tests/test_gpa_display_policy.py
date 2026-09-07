"""Official CGPA is display metadata, not a replacement for course mathematics."""
from copy import deepcopy
from dataclasses import asdict

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from core.gpa_engine import calculate_gpa
from models.course import Course
from services.academic_summary_service import (
    AcademicSummaryValidationError, build_academic_summary,
)
from services.transcript_workflow import run_transcript_workflow


def courses(aa_weight=23):
    return [
        Course(code="CS101", name="First", gpa_credit=aa_weight, grade="AA", semester="2024-2025 Güz", source_order=0),
        Course(code="CS102", name="Second", gpa_credit=100-aa_weight, grade="BB", semester="2024-2025 Güz", source_order=1),
    ]


@pytest.mark.parametrize("official, aa_weight, derived", [
    (3.24, 23, 3.23), (None, 23, 3.23), (3.24, 24, 3.24), (0.0, 23, 3.23),
])
def test_domain_keeps_official_and_derived_separate_without_mutation(official, aa_weight, derived):
    rows = courses(aa_weight)
    before = deepcopy(rows)
    summary = build_academic_summary(rows, official_cgpa=official)
    assert summary.official_cgpa == official
    assert summary.derived_cgpa == pytest.approx(derived)
    assert summary.current_gpa == pytest.approx(derived)  # Legacy calculation contract.
    assert summary.semesters[0].gpa == pytest.approx(derived)
    assert calculate_gpa(rows) == pytest.approx(derived)
    assert rows == before


@pytest.mark.parametrize("official", [3.24, None, 0.0])
def test_summary_api_preserves_both_gpas(official):
    with TestClient(create_app()) as client:
        response = client.post("/api/academic/summary", json={
            "courses": [asdict(c) for c in courses()], "official_cgpa": official,
        })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["official_cgpa"] == official
    assert body["derived_cgpa"] == pytest.approx(3.23)
    assert body["current_gpa"] == pytest.approx(3.23)


def test_legacy_summary_request_keeps_course_fallback():
    with TestClient(create_app()) as client:
        body = client.post("/api/academic/summary", json={"courses": [asdict(c) for c in courses()]}).json()
    assert body["official_cgpa"] is None
    assert body["derived_cgpa"] == pytest.approx(3.23)


@pytest.mark.parametrize("official", [-0.1, 4.01, True, "3.24"])
def test_summary_rejects_invalid_official_values(official):
    with TestClient(create_app()) as client:
        response = client.post("/api/academic/summary", json={
            "courses": [asdict(c) for c in courses()], "official_cgpa": official,
        })
    assert response.status_code == 422
    with pytest.raises(AcademicSummaryValidationError):
        build_academic_summary(courses(), official_cgpa=official)


@pytest.mark.parametrize("official", [float("nan"), float("inf")])
def test_domain_rejects_non_finite_official_values(official):
    with pytest.raises(AcademicSummaryValidationError):
        build_academic_summary(courses(), official_cgpa=official)


def test_rounding_difference_is_not_an_alarm():
    text = """Course Credit ECTS Grade
CS101 First 0.23 1 AA
CS102 Second 0.77 2 BB
Genel Not Ortalamasi (GNO / CGPA): 3.24 / 4.00
"""
    result = run_transcript_workflow(text, gpa_weighting_field="local_credit")
    assert result.extraction.document.summary.cgpa == 3.24
    assert calculate_gpa(result.courses) == pytest.approx(3.23)
    assert not any(issue.code == "official_gpa_mismatch" for issue in result.issues)


def test_large_official_gap_is_warning_without_mutating_courses():
    """Gaps can exceed 0.10; keep both values and never rewrite course math."""
    text = """Course Credit ECTS Grade
CS101 First 0.23 1 AA
CS102 Second 0.77 2 BB
Genel Not Ortalamasi (GNO / CGPA): 2.90 / 4.00
"""
    result = run_transcript_workflow(text, gpa_weighting_field="local_credit")
    before = deepcopy(result.courses)
    assert result.extraction.document.summary.cgpa == 2.9
    assert calculate_gpa(result.courses) == pytest.approx(3.23)
    assert any(issue.code == "official_gpa_mismatch" for issue in result.issues)
    summary = build_academic_summary(result.courses, official_cgpa=2.9)
    assert summary.official_cgpa == 2.9
    assert summary.derived_cgpa == pytest.approx(3.23)
    assert summary.current_gpa == pytest.approx(3.23)
    assert result.courses == before


def test_summary_metadata_never_changes_planner_results():
    with TestClient(create_app()) as client:
        payload = {"courses": [asdict(c) for c in courses()], "target_gpa": 3.5, "max_grade": "AA", "strategy": "min_courses"}
        before = client.post("/api/academic/target-plan", json=payload)
        client.post("/api/academic/summary", json={"courses": payload["courses"], "official_cgpa": 3.24})
        after = client.post("/api/academic/target-plan", json=payload)
    assert before.status_code == after.status_code == 200
    assert before.json() == after.json()
    assert after.json()["current_gpa"] == pytest.approx(3.23)
