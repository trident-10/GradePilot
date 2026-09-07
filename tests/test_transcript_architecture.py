import ast
from dataclasses import asdict
from pathlib import Path

import pdfplumber
import pytest
from fpdf import FPDF

from parsers.document_parser import extract_transcript
from parsers.pdf_layout import extract_page_blocks, extract_page_text
from services.transcript_presentation import present_transcript
from services.transcript_workflow import run_transcript_workflow
from validation.transcript_validation import validate_transcript


def test_extraction_validation_workflow_and_presentation_are_independent():
    text = "Course Credit ECTS Grade\nCENG101 Programming 3 6 BA\nCENG102 Algorithms ? 7 BB"
    extraction = extract_transcript(text)
    assert len(extraction.rows) == 2  # Invalid input remains available for inspection.
    assert not hasattr(extraction, "requires_credit_selection")
    assert not hasattr(extraction, "warnings")
    before = asdict(extraction)
    report = validate_transcript(extraction)
    assert report.errors[0].code == "invalid_credit_cells"
    assert report.errors[0].row_index == 2
    assert asdict(extraction) == before

    valid = "Course Credit ECTS Grade\nCENG101 Programming 3 6 BA"
    decision = run_transcript_workflow(valid)
    assert decision.step == "weighting_required"
    assert not hasattr(decision, "credit_options")
    response = present_transcript(decision)
    assert response.requires_credit_selection
    assert [o.label for o in response.credit_options] == ["Kredi", "AKTS / ECTS"]


def test_fact_parser_has_no_application_or_presentation_imports():
    modules = ["parsers/document_parser.py", "parsers/rows.py", "parsers/headers.py",
               "parsers/generic_analyzer.py", "parsers/pdf_layout.py",
               "validation/transcript_validation.py"]
    root = Path(__file__).resolve().parents[1]
    for module in modules:
        tree = ast.parse((root / module).read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith(("api.", "services.")), module


@pytest.mark.parametrize("hours", ["3+2", "3 + 2", "3+0"])
def test_combined_hours_never_become_credit(hours):
    decision = run_transcript_workflow(
        f"Course T+U Credit ECTS Grade\nCENG101 Programming {hours} 4 6 BA",
        gpa_weighting_field="local_credit",
    )
    assert decision.courses[0].local_credit == 4
    assert decision.courses[0].ects == 6
    assert decision.courses[0].name == "Programming"


@pytest.mark.parametrize("code", ["1234567", "CS_1001", "A1.2", "INF-10001"])
def test_identifiers_use_table_schema_instead_of_department_regex(code):
    decision = run_transcript_workflow(
        f"Course Code | Course Name | T+U | Credit | ECTS | Unknown Metadata | Letter Grade\n"
        f"{code} | Programming Languages | 3+2 | 4 | 6 | transfer accepted | BA",
        gpa_weighting_field="local_credit",
    )
    assert decision.courses[0].code == code
    assert decision.courses[0].local_credit == 4
    assert decision.courses[0].ects == 6
    assert decision.courses[0].name == "Programming Languages"


def test_unknown_plain_text_headers_still_abstain():
    decision = run_transcript_workflow(
        "Course Credit ECTS Unknown Grade\nCENG101 Programming 3 6 99 BA"
    )
    assert decision.step == "mapping_required"


def _mixed_layout_pdf(path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=9)
    # A long heading and a full-width course precede the parallel tables.
    pdf.text(10, 15, "Official transcript with a full width heading shared by the entire academic document")
    pdf.text(10, 24, "2023-2024 Fall")
    pdf.text(10, 30, "Course Credit ECTS Grade")
    pdf.text(10, 36, "CENG100 Introductory course with a long name that reaches across both later tables 3 6 AA")
    for x, term, code in [(10, "Fall", 101), (110, "Spring", 103)]:
        for y, text in [(50, f"2024-2025 {term}"), (56, "Course Credit ECTS Grade"),
                        (62, f"CENG{code} Programming 3 6 BA"), (68, f"CENG{code + 1} Algorithms 4 7 BB")]:
            pdf.text(x, y, text)
    pdf.text(10, 82, "Explanation: this full width note belongs to the document and must remain intact")
    pdf.text(10, 96, "2025-2026 Fall")
    pdf.text(10, 102, "Course Credit ECTS Grade")
    pdf.text(10, 108, "CENG201 A final full width course after the parallel tables 3 6 AA")
    path.write_bytes(bytes(pdf.output()))


def test_local_blocks_keep_full_width_content_and_never_crop(tmp_path, monkeypatch):
    path = tmp_path / "mixed-layout.pdf"
    _mixed_layout_pdf(path)
    def forbidden(*args, **kwargs):
        raise AssertionError("Page cropping is forbidden")
    monkeypatch.setattr(pdfplumber.page.Page, "crop", forbidden)
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        blocks = extract_page_blocks(page)
        original = page.dedupe_chars().extract_words(x_tolerance=2, y_tolerance=3)
        preserved = [word for block in blocks for column in block.columns for line in column for word in line]
        key = lambda w: (w["text"], w["x0"], w["top"])
        assert sorted(map(key, preserved)) == sorted(map(key, original))
        parallel = [block for block in blocks if len(block.columns) > 1]
        assert len(parallel) == 1
        assert parallel[0].bbox[1] > 100
        assert parallel[0].bbox[3] < 220
        text = extract_page_text(page)
    assert "Explanation: this full width note belongs to the document and must remain intact" in text
    assert "Official transcript with a full width heading shared by the entire academic document" in text
    decision = run_transcript_workflow(text, gpa_weighting_field="local_credit")
    assert [c.code for c in decision.courses] == ["CENG100", "CENG101", "CENG102", "CENG103", "CENG104", "CENG201"]
    assert [c.semester for c in decision.courses] == ["2023-2024 Güz", "2024-2025 Güz", "2024-2025 Güz",
                                                   "2024-2025 Bahar", "2024-2025 Bahar", "2025-2026 Güz"]


def test_geometric_cells_preserve_unknown_columns_and_numeric_codes(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=8)
    for y, cells in [(20, ["Course Code", "Course Name", "T+U", "Credit", "ECTS", "Unknown", "Grade"]),
                     (30, ["1234567", "Programming", "3+2", "4", "6", "approved", "BA"])]:
        for x, text in zip([10, 40, 80, 100, 120, 145, 175], cells):
            pdf.text(x, y, text)
    path = tmp_path / "cells.pdf"
    path.write_bytes(bytes(pdf.output()))
    with pdfplumber.open(path) as doc:
        text = extract_page_text(doc.pages[0])
    decision = run_transcript_workflow(text, gpa_weighting_field="local_credit")
    assert decision.courses[0].code == "1234567"
    assert decision.courses[0].local_credit == 4


def test_missing_cell_is_preserved_and_reported_without_shifting():
    extraction = extract_transcript(
        "Code | Course Name | Credit | ECTS | Grade\n123456 | Programming | | 6 | BA"
    )
    assert extraction.rows[0].parts == ["123456", "Programming", "?", "6", "BA"]
    assert validate_transcript(extraction).errors[0].code == "invalid_credit_cells"


def test_non_gpa_status_uses_grade_cell_even_with_unknown_column_before_it():
    extraction = extract_transcript(
        "Code | Course Name | Credit | ECTS | Unknown | Grade\n"
        "123456 | Programming | 3 | 6 | approved | BA\n"
        "123457 | Internship | 0 | 6 | approved | MU"
    )
    report = validate_transcript(extraction)
    assert not report.errors
    assert any(issue.code == "excluded_courses" and issue.count == 1 for issue in report.issues)


def test_parallel_columns_restore_shared_context_instead_of_leaking_left_term():
    text = """
2023-2024 Fall
Course Credit ECTS Grade
[[TABLE_BEGIN]]
2024-2025 Spring
CENG101 Programming 3 6 BA
[[TABLE_NEXT]]
CENG102 Algorithms 4 7 BB
[[TABLE_END]]
CENG103 Databases 3 6 AA
"""
    decision = run_transcript_workflow(text, gpa_weighting_field="local_credit")
    assert [c.semester for c in decision.courses] == ["2024-2025 Bahar", "2023-2024 Güz", "2023-2024 Güz"]


def test_two_separate_parallel_blocks_do_not_capture_the_content_between_them(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=9)
    for top, year, base in [(20, "2023-2024", 100), (80, "2024-2025", 200)]:
        for x, term, code in [(10, "Fall", base + 1), (110, "Spring", base + 2)]:
            pdf.text(x, top, f"{year} {term}")
            pdf.text(x, top + 6, "Course Credit ECTS Grade")
            pdf.text(x, top + 12, f"CENG{code} Programming 3 6 BA")
    pdf.text(10, 60, "Explanation: a full width section separates the independent table blocks below and above")
    path = tmp_path / "independent-blocks.pdf"
    path.write_bytes(bytes(pdf.output()))
    with pdfplumber.open(path) as doc:
        blocks = extract_page_blocks(doc.pages[0])
        text = extract_page_text(doc.pages[0])
    assert len([block for block in blocks if len(block.columns) > 1]) == 2
    assert "Explanation: a full width section separates the independent table blocks below and above" in text
    decision = run_transcript_workflow(text, gpa_weighting_field="local_credit")
    assert [c.semester for c in decision.courses] == ["2023-2024 Güz", "2023-2024 Bahar", "2024-2025 Güz", "2024-2025 Bahar"]
