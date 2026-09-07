import io

import pytest
from fastapi.testclient import TestClient
from fpdf import FPDF

from api.main import create_app
from core.gpa_engine import calculate_gpa
from parsers.document_parser import extract_transcript
from services.transcript_errors import TranscriptStructureError
from services.transcript_workflow import analyze_and_parse_transcript, run_transcript_workflow
from validation.mapping_validation import MappingValidationError, validate_mapping
from validation.transcript_validation import validate_transcript


COURSES = "2024-2025 Fall\nCourse Credit ECTS Grade\nCENG101 Programming 3 6 BA\n"


@pytest.mark.parametrize("summary", [
    "CGPA: 3.08 Total Credits: 150 Total ECTS: 240",
    "GANO: 3,08 Toplam Kredi: 150 Toplam AKTS: 240",
    "CGPA / Total Credits / Total ECTS\n3.08 / 150 / 240",
    "GANO | Toplam Kredi | Toplam AKTS\n3,08 | 150 | 240",
    "Overall Summary\nCGPA\n3.08\nTotal Credits\n150\nTotal ECTS\n240",
    "CGPA: 3.08\nTotal Credits: 150\nTotal ECTS: 240",
    "Genel Not Ortalaması (CGPA): 3,08 Toplam Kredi: 150 Toplam AKTS: 240",
])
def test_official_values_are_read_as_printed_before_weighting(summary):
    result = analyze_and_parse_transcript(COURSES + summary)
    assert result.requires_credit_selection
    assert result.document.summary.cgpa == 3.08
    assert result.document.summary.total_local_credit == 150
    assert result.document.summary.total_ects == 240
    assert len(result.document.semesters) == 1
    assert result.document.semesters[0].course_source_orders == [0]
    assert len(result.document.observations) == 3
    assert all(value.source_line >= 3 for value in result.document.observations)


def test_semester_summaries_do_not_overwrite_overall_summary():
    text = COURSES + """Semester GPA: 3.50 Total Credits: 18 Total ECTS: 30
2024-2025 Spring
CENG102 Algorithms 4 7 AA
Dönem Ortalaması: 3,70 Toplam Kredi: 20 Toplam AKTS: 32
Overall Summary
CGPA: 3.08 Total Credits: 150 Total ECTS: 240
"""
    result = analyze_and_parse_transcript(text, gpa_weighting_field="local_credit")
    semesters = result.document.semesters
    assert [s.label for s in semesters] == ["2024-2025 Güz", "2024-2025 Bahar"]
    assert [s.summary.gpa for s in semesters] == [3.5, 3.7]
    assert [s.summary.local_credit for s in semesters] == [18, 20]
    assert [s.summary.ects for s in semesters] == [30, 32]
    assert [len(s.courses) for s in semesters] == [1, 1]
    assert result.document.summary.cgpa == 3.08
    assert result.document.summary.total_local_credit == 150
    assert calculate_gpa(result.courses) == pytest.approx(3.79, abs=0.01)
    assert sum(c.gpa_credit for c in result.courses) == 7


def test_official_values_are_preserved_across_credit_choices():
    text = COURSES + "CGPA: 3.08 Total Credits: 150 Total ECTS: 240"
    local = analyze_and_parse_transcript(text, gpa_weighting_field="local_credit")
    ects = analyze_and_parse_transcript(text, gpa_weighting_field="ects")
    assert local.courses[0].gpa_credit == 3
    assert ects.courses[0].gpa_credit == 6
    assert local.document.summary == ects.document.summary
    assert local.document.observations == ects.document.observations


def test_unlabelled_numbers_and_course_grade_points_are_not_official_values():
    extraction = extract_transcript(COURSES + "3.08 / 150 / 240\nAA=4.00 BA=3.50")
    assert extraction.document.summary.cgpa is None
    assert extraction.document.summary.total_local_credit is None
    assert extraction.document.summary.total_ects is None
    assert extraction.document.observations == []


def test_duplicate_official_values_are_preserved_and_conflicts_reported():
    extraction = extract_transcript(COURSES + "CGPA: 3.08\nCGPA: 3.10\nTotal ECTS: 240\nTotal ECTS: 240")
    assert extraction.document.summary.cgpa is None
    assert extraction.document.summary.total_ects == 240
    assert len(extraction.document.observations) == 4
    report = validate_transcript(extraction)
    assert not report.errors
    assert any(issue.code == "conflicting_official_values" for issue in report.issues)


def test_summary_only_semester_is_modelled_without_invented_courses():
    document = extract_transcript(COURSES + "2024-2025 Spring\nSemester GPA: 3.20 Total Credits: 18").document
    assert len(document.semesters) == 2
    assert document.semesters[1].summary.gpa == 3.2
    assert document.semesters[1].courses == []
    assert document.semesters[1].course_source_orders == []


def test_official_totals_cannot_be_misrecognized_as_course_codes():
    result = analyze_and_parse_transcript(COURSES + "Overall Summary\nAKTS 240\nKredi 150\nGANO 3.08")
    assert result.document.summary.total_ects == 240
    assert result.document.summary.total_local_credit == 150
    assert result.document.summary.cgpa == 3.08


def test_local_table_summary_context_is_scoped():
    text = """[[TABLE_BEGIN]]
2024-2025 Fall
Course Credit ECTS Grade
CENG101 Programming 3 6 BA
Semester GPA: 3.50 Total ECTS: 30
[[TABLE_NEXT]]
2024-2025 Spring
Course Credit ECTS Grade
CENG102 Algorithms 4 7 BB
Semester GPA: 3.00 Total ECTS: 32
[[TABLE_END]]
CGPA: 3.08 Total Credits: 150 Total ECTS: 240
"""
    doc = extract_transcript(text).document
    assert [s.summary.gpa for s in doc.semesters] == [3.5, 3]
    assert [s.summary.ects for s in doc.semesters] == [30, 32]
    assert doc.summary.cgpa == 3.08


@pytest.mark.parametrize("mapping, code", [
    ({}, "empty_mapping"),
    ({"hours": -1}, "unsupported_mapping"),
    ({"local_credit": -1, "ects": -1}, "duplicate_mapping"),
    ({"local_credit": -99}, "invalid_mapping"),
    ({"local_credit": True}, "invalid_mapping"),
    ({"local_credit": "-1"}, "invalid_mapping"),
])
def test_user_mapping_failures_are_not_document_issues(mapping, code):
    with pytest.raises(MappingValidationError) as caught:
        validate_mapping(mapping, {-1, -2})
    assert caught.value.code == code
    assert not isinstance(caught.value, TranscriptStructureError)
    assert not hasattr(caught.value, "issue")


def test_workflow_mapping_error_does_not_mark_valid_document_invalid():
    extraction = extract_transcript(COURSES)
    assert not validate_transcript(extraction).errors
    with pytest.raises(MappingValidationError, match="same numeric column"):
        run_transcript_workflow(COURSES, semantic_field_positions={"local_credit": -1, "ects": -1})
    with pytest.raises(MappingValidationError):
        run_transcript_workflow(COURSES, gpa_weighting_field="rel:bad")
    with pytest.raises(MappingValidationError):
        run_transcript_workflow(COURSES, gpa_weighting_field="invalid")


def test_incomplete_selected_user_column_is_a_mapping_error():
    text = "Course Value One Value Two Grade\nCENG101 Programming 3 6 BA\nCENG102 Algorithms 7 BB"
    assert not validate_transcript(extract_transcript(text)).errors
    with pytest.raises(MappingValidationError) as caught:
        run_transcript_workflow(text, semantic_field_positions={"local_credit": -2}, gpa_weighting_field="local_credit")
    assert caught.value.code == "incomplete_mapping"


def _pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    for i, line in enumerate(text.splitlines()):
        pdf.text(10, 20 + 6 * i, line)
    return bytes(pdf.output())


def test_pdf_api_returns_official_summary_and_semesters_at_every_stage():
    data = _pdf(COURSES + "Semester GPA: 3.50 Total ECTS: 30\nOverall Summary\nCGPA: 3.08 Total Credits: 150 Total ECTS: 240")
    with TestClient(create_app()) as client:
        for form in ({}, {"weighting_field": "credit"}, {"weighting_field": "ects"}):
            response = client.post("/api/transcripts/analyze", files={"file": ("sample.pdf", io.BytesIO(data), "application/pdf")}, data=form)
            assert response.status_code == 200, response.text
            body = response.json()
            assert body["official_summary"]["cgpa"] == 3.08
            assert body["official_summary"]["total_local_credit"] == 150
            assert body["official_summary"]["total_ects"] == 240
            assert body["semesters"][0]["official_summary"]["gpa"] == 3.5
            assert body["semesters"][0]["course_source_orders"] == [0]


def test_api_error_categories_distinguish_document_and_mapping():
    ambiguous = _pdf("Course Value One Value Two Grade\nCENG101 Programming 3 6 BA")
    invalid = _pdf("Course Credit ECTS Grade\nCENG101 Programming ? 6 BA")
    with TestClient(create_app()) as client:
        response = client.post("/api/transcripts/analyze", files={"file": ("sample.pdf", ambiguous, "application/pdf")},
                               data={"local_credit_field": "column_a", "ects_field": "column_a"})
        assert response.status_code == 400
        assert response.json()["error_type"] == "invalid_mapping_request"
        assert response.json()["code"] == "duplicate_mapping"
        response = client.post("/api/transcripts/analyze", files={"file": ("sample.pdf", invalid, "application/pdf")})
        assert response.status_code == 400
        assert response.json()["error_type"] == "invalid_transcript"
        assert response.json()["code"] == "invalid_credit_cells"


def test_official_values_survive_manual_mapping_workflow():
    text = "Course Value One Value Two Grade\nCENG101 Programming 3 6 BA\nCGPA: 3.08 Total Credits: 150 Total ECTS: 240"
    pdf = _pdf(text)
    forms = [{}, {"local_credit_field": "column_a", "ects_field": "column_b"},
             {"local_credit_field": "column_a", "ects_field": "column_b", "weighting_field": "credit"}]
    with TestClient(create_app()) as client:
        for form, status in zip(forms, ["manual_mapping", "credit_selection", "confirmation"]):
            response = client.post("/api/transcripts/analyze", files={"file": ("sample.pdf", pdf, "application/pdf")}, data=form)
            assert response.status_code == 200, response.text
            assert response.json()["status"] == status
            assert response.json()["official_summary"]["cgpa"] == 3.08
            assert response.json()["official_summary"]["total_ects"] == 240
