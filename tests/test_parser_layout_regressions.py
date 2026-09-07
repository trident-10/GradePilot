import io

import pytest
from fastapi.testclient import TestClient
from fpdf import FPDF

from api.main import create_app
from core.gpa_engine import calculate_gpa
from core.semester_engine import calculate_semester_gpas
from parsers.transcript_parser import (
    TranscriptStructureError, analyze_and_parse_transcript, extract_text_from_pdf,
    keep_latest_attempts,
)
from services.transcript_service import process_transcript


@pytest.mark.parametrize("heading, expected", [
    ("2024-2025 Güz Dönemi", "2024-2025 Güz"),
    ("2024 / 2025 GÜZ YARIYILI", "2024-2025 Güz"),
    ("Spring Semester 2024–2025", "2024-2025 Bahar"),
    ("2024-2025 Summer", "2024-2025 Yaz"),
    ("2024-2025\nFall Semester", "2024-2025 Güz"),
    ("1. Yarıyıl", "1. Yarıyıl"),
])
def test_semester_heading_variants(heading, expected):
    result = analyze_and_parse_transcript(
        f"{heading}\nCourse Credit ECTS Grade\nCENG101 Programming 3 6 BA",
        gpa_weighting_field="local_credit",
    )
    assert result.courses[0].semester == expected
    assert calculate_semester_gpas(result.courses)[0]["semester"] == expected


def test_wrapped_rows_decimal_comma_and_course_number_in_name():
    text = """
2024-2025 Güz Dönemi
Ders Kredi AKTS Harf Notu
1. CENG - 101 Introduction to
Computer Science 3,5 6,0 BA
MATH102 Calculus 2 4,0 7,5 BB
2024-2025 Bahar Dönemi
CENG 102 Data
Structures
4,5 6,5 AA
"""
    result = analyze_and_parse_transcript(text, gpa_weighting_field="local_credit")
    assert [c.code for c in result.courses] == ["CENG101", "MATH102", "CENG102"]
    assert [c.name for c in result.courses] == ["Introduction to Computer Science", "Calculus 2", "Data Structures"]
    assert [c.gpa_credit for c in result.courses] == [3.5, 4, 4.5]
    assert result.courses[1].ects == 7.5
    assert result.courses[2].semester == "2024-2025 Bahar"
    assert calculate_gpa(result.courses) == pytest.approx(3.52, abs=0.01)


@pytest.mark.parametrize("header, cells, credit, ects", [
    ("Course Credit ECTS Score Grade", "3 6 85 BA", 3, 6),
    ("Course Credit ECTS Numeric Grade Letter Grade", "3 6 85 BA", 3, 6),
    ("Course Grade Credit ECTS", "BA 3 6", 3, 6),
    ("Course ECTS Grade Credit", "6 BA 3", 3, 6),
    ("Course Credit Grade ECTS", "3 BA 6", 3, 6),
    ("Course ECTS Credit Letter Grade Points", "6 3 BA 10.5", 3, 6),
    ("Ders T U Kredi AKTS Harf Notu", "2 1 3 6 BA", 3, 6),
])
def test_headers_determine_credit_not_distance_from_grade(header, cells, credit, ects):
    result = analyze_and_parse_transcript(
        f"{header}\nCENG101 Programming {cells}", gpa_weighting_field="local_credit",
    )
    assert result.courses[0].local_credit == credit
    assert result.courses[0].ects == ects
    assert result.courses[0].name == "Programming"


def test_unknown_intervening_column_requires_mapping():
    preview = analyze_and_parse_transcript(
        "Course Credit ECTS Unknown Grade\nCENG101 Programming 3 6 85 BA"
    )
    assert preview.requires_manual_mapping
    assert not preview.credit_options


def test_changed_headers_are_resolved_per_semester():
    text = """
2024-2025 Fall
Course Credit ECTS Grade
CENG101 Programming 3 6 BA
2024-2025 Spring
Course ECTS Credit Score Grade
CENG102 Algorithms 7 4 80 BB
"""
    result = analyze_and_parse_transcript(text, gpa_weighting_field="local_credit")
    assert [c.local_credit for c in result.courses] == [3, 4]
    assert [c.ects for c in result.courses] == [6, 7]
    assert calculate_gpa(result.courses) == pytest.approx(3.21, abs=0.01)


def test_cankaya_decimal_credit_and_grade_at_end():
    text = "Çankaya University\n2024/2025 GÜZ\nCENG111 Programming Z İng. 3 2 3,5 6,0 BA"
    result = analyze_and_parse_transcript(text, gpa_weighting_field="local_credit")
    assert result.courses[0].local_credit == 3.5
    assert result.courses[0].semester == "2024-2025 Güz"
    assert result.courses[0].name == "Programming"


def test_institution_name_does_not_force_wrong_parser():
    text = "Çankaya University\nCourse Credit ECTS Grade\nCENG101 Programming 3 6 BA"
    result = analyze_and_parse_transcript(text, gpa_weighting_field="local_credit")
    assert result.format_name == "generic"
    assert result.requires_user_confirmation
    assert result.courses[0].local_credit == 3


@pytest.mark.parametrize("bad_row", [
    "CENG102 Algorithms ? 6 BB",
    "CENG102 Algorithms 3 6 B+",
    "CENG102 Algorithms 3 6",
    "CENG102 Algorithms -3 6 BB",
])
def test_partial_or_unsupported_rows_cannot_silently_change_gpa(bad_row):
    text = f"Course Credit ECTS Grade\nCENG101 Programming 3 6 BA\n{bad_row}"
    with pytest.raises(TranscriptStructureError):
        analyze_and_parse_transcript(
            text, gpa_weighting_field="local_credit",
            semantic_field_positions={"local_credit": -2, "ects": -1},
        )


def test_explicit_non_gpa_course_is_reported():
    result = analyze_and_parse_transcript(
        "Course Credit ECTS Grade\nCENG101 Programming 3 6 BA\nENG101 English 0 4 MU",
        gpa_weighting_field="local_credit",
    )
    assert len(result.courses) == 1
    assert any("1 dersin" in warning for warning in result.warnings)
    assert result.requires_user_confirmation


def test_zero_credit_is_valid_not_an_unreadable_field():
    result = analyze_and_parse_transcript(
        "Course Credit ECTS Grade\nCENG101 Internship 0 6 AA",
        gpa_weighting_field="local_credit",
    )
    assert result.courses[0].local_credit == 0


def test_missing_credit_cell_cannot_shift_the_other_field_into_its_place():
    with pytest.raises(TranscriptStructureError, match="Kredi/AKTS"):
        analyze_and_parse_transcript(
            "Course Credit ECTS Grade\nCENG101 Programming 3 6 BA\nCENG102 Algorithms 4 BB"
        )


def test_language_course_name_is_not_removed_as_metadata():
    result = analyze_and_parse_transcript(
        "Course Credit ECTS Grade\nENG101 English 3 6 BA", gpa_weighting_field="local_credit",
    )
    assert result.courses[0].name == "English"


def test_summary_does_not_reset_column_mapping():
    result = analyze_and_parse_transcript("""
2024-2025 Fall
Course Credit ECTS Grade
CENG101 Programming 3 6 BA
Total Credits 3
2024-2025 Spring
CENG102 Algorithms 4 7 BB
""", gpa_weighting_field="local_credit")
    assert len(result.courses) == 2
    assert result.courses[1].semester == "2024-2025 Bahar"


def _layout_pdf(*, two_columns=False, multipage=False):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=9)
    for column in range(2):
        if multipage and column:
            pdf.add_page()
        x = 10 + (100 * column if two_columns else 0)
        y = 20 if two_columns or multipage else 20 + column * 50
        lines = [
            f"2024-2025 {'Fall' if column == 0 else 'Spring'}",
            "Course Credit ECTS Grade",
            f"CENG{101 + column * 2} Programming 3 6 BA",
            f"CENG{102 + column * 2} Algorithms 4 7 BB",
        ]
        for index, line in enumerate(lines):
            pdf.text(x, y + index * 6, line)
    return bytes(pdf.output())


@pytest.mark.parametrize("layout", ["single", "columns", "pages"])
def test_real_pdf_upload_to_semester_calculation(layout, tmp_path):
    data = _layout_pdf(two_columns=layout == "columns", multipage=layout == "pages")
    path = tmp_path / "transcript.pdf"
    path.write_bytes(data)
    result = process_transcript(str(path), gpa_weighting_field="local_credit")
    assert [c.code for c in result.courses] == ["CENG101", "CENG102", "CENG103", "CENG104"]
    assert [c.semester for c in result.courses] == ["2024-2025 Güz"] * 2 + ["2024-2025 Bahar"] * 2
    assert calculate_gpa(result.courses) == pytest.approx(3.21, abs=0.01)
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/transcripts/analyze", files={"file": ("transcript.pdf", io.BytesIO(data), "application/pdf")},
            data={"weighting_field": "credit"},
        )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "confirmation"
    assert len(response.json()["courses"]) == 4


def test_existing_cankaya_pdf_still_extracts():
    text = extract_text_from_pdf("tests/fixtures/sample_cankaya.pdf")
    result = analyze_and_parse_transcript(text, gpa_weighting_field="local_credit")
    assert len(result.courses) == 2
    assert result.courses[0].semester == "2024-2025 Güz"
    assert calculate_gpa(result.courses) == 2


def test_newest_first_transcript_uses_actual_latest_attempt():
    result = analyze_and_parse_transcript("""
2025-2026 Fall
Course Credit ECTS Grade
CENG101 Programming 3 6 AA
2024-2025 Fall
CENG101 Programming 3 6 FF
""", gpa_weighting_field="local_credit")
    for courses in (result.courses, list(reversed(result.courses))):
        latest = keep_latest_attempts(courses)
        assert len(latest) == 1
        assert latest[0].grade == "AA"
        assert calculate_gpa(latest) == 4


def test_unsplit_side_by_side_rows_cannot_be_one_course():
    with pytest.raises(TranscriptStructureError, match="Yan yana"):
        analyze_and_parse_transcript(
            "Course Credit ECTS Grade\nCENG101 Programming 3 6 BA CENG102 Algorithms 4 7 BB",
            gpa_weighting_field="local_credit",
        )


def test_scanned_page_in_mixed_pdf_is_not_silently_skipped(tmp_path):
    from PIL import Image
    from input.pdf_input import PdfValidationError

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.text(10, 20, "Course Credit ECTS Grade")
    pdf.text(10, 30, "CENG101 Programming 3 6 BA")
    pdf.add_page()
    pdf.image(Image.new("RGB", (100, 100), "white"), x=10, y=10, w=100)
    path = tmp_path / "mixed.pdf"
    path.write_bytes(bytes(pdf.output()))
    with pytest.raises(PdfValidationError, match="PDF okunamadı"):
        process_transcript(str(path), gpa_weighting_field="local_credit")


def test_pdf_name_wraps_below_completed_numeric_cells(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    pdf.text(10, 20, "Course Credit ECTS Grade")
    pdf.text(10, 30, "CENG101")
    pdf.text(35, 30, "Introduction to")
    pdf.text(100, 30, "3 6 BA")
    pdf.text(35, 35, "Computer Science")
    path = tmp_path / "wrapped.pdf"
    path.write_bytes(bytes(pdf.output()))
    result = process_transcript(str(path), gpa_weighting_field="local_credit")
    assert result.courses[0].name == "Introduction to Computer Science"
    assert result.courses[0].local_credit == 3
