"""Anonymous regression cases for staggered bilingual transcript tables."""
from dataclasses import asdict

import pdfplumber
import pytest
from fpdf import FPDF

from parsers.document_parser import extract_transcript
from parsers.official_summary import extract_official_document
from parsers.pdf_layout import extract_page_blocks, extract_page_text
from services.transcript_workflow import run_transcript_workflow
from validation.mapping_validation import MappingValidationError
from validation.transcript_validation import validate_transcript


def _pdf(path, university="Example University"):
    pdf = FPDF(unit="pt", format=(600, 840))
    pdf.add_page()
    pdf.set_font("helvetica", size=7)
    pdf.text(20, 30, university)
    pdf.text(20, 50, "Cumulative GPA: 2.59")
    pdf.text(20, 70, "ISCED Code")
    pdf.text(300, 70, "Credits Completed")
    pdf.text(20, 79, ":0714")
    pdf.text(300, 79, ":82")
    for term, top in (("Fall", 120), ("Spring", 270)):
        for x, text in zip((20, 263, 325, 447, 480, 510, 552),
                           (f"2024-2025 {term}", "Course Status", "Language", "ECTS", "Grade", "Points", "Comment")):
            pdf.text(x, top, text)
        # A second, offset baseline in the same header band.
        for x, text in zip((378, 402, 426), ("T", "U", "UK")):
            pdf.text(x, top + 5, text)
        for x, text in zip((20, 263, 325, 447, 480, 510, 552),
                           (f"(2024-2025 {term} Term)", "(Course Status)", "(Language)", "(ECTS)", "(Grade)", "(Points)", "(Comment)")):
            pdf.text(x, top + 10, text)
        for row, (code, title, grade, points, status) in enumerate((
            ("CS 101", "Computer Programming I", "BB", "12", "G"),
            ("MATH 102", "Calculus for Engineers II", "BA", "14", "TKR G"),
            ("*PREP 114", "Language Preparation", "S", "(64,0)", "-"),
        )):
            for x, text in zip((25, 78, 280, 332, 380, 405, 430, 453, 484, 514, 555),
                               (code, title, "Z", "Eng.", "3", "2", "4", "6", grade, points, status)):
                pdf.text(x, top + 23 + row * 22, text)
            pdf.text(78, top + 31 + row * 22, "(Translated course title)")
        pdf.text(20, top + 100, "DNO:3.25 GNO:2.59 TUK:8 TAKTS:12")
        pdf.text(20, top + 110, "(GPA) (CGPA) (TNK) (TECTS)")
    pdf.add_page()
    pdf.text(20, 40, "Explanations")
    pdf.text(20, 55, "PREP 114 B2 Level or EX grade from PREP 150 are considered")
    pdf.text(440, 55, "50 - 59 DC 1.50")
    pdf.text(20, 75, "UK: National Credits")
    path.write_bytes(bytes(pdf.output()))


@pytest.mark.parametrize("university", ["Example University", "CANKAYA UNIVERSITY"])
def test_staggered_headers_work_without_institution_template(tmp_path, monkeypatch, university):
    path = tmp_path / "bilingual.pdf"
    _pdf(path, university)
    def no_crop(*args, **kwargs):
        raise AssertionError("Do not divide the page")
    monkeypatch.setattr(pdfplumber.page.Page, "crop", no_crop)
    with pdfplumber.open(path) as pdf:
        assert all(len(block.columns) == 1 for block in extract_page_blocks(pdf.pages[0]))
        text = "\n".join(extract_page_text(page) for page in pdf.pages)
    extraction = extract_transcript(text)
    assert len(extraction.rows) == 6
    assert len(extraction.courses) == 4
    assert [(c.code, c.local_credit, c.ects) for c in extraction.courses] == [
        ("CS101", 4, 6), ("MATH102", 4, 6), ("CS101", 4, 6), ("MATH102", 4, 6),
    ]
    assert extraction.courses[0].name == "Computer Programming I (Translated course title)"
    assert extraction.courses[1].name == "Calculus for Engineers II (Translated course title)"
    assert all(c.semester for c in extraction.courses)
    assert [(i.code, i.count) for i in validate_transcript(extraction).issues] == [("excluded_courses", 2)]
    assert extraction.document.summary.cgpa == 2.59
    assert extraction.document.summary.total_local_credit == 82
    assert len(extraction.document.semesters) == 2
    assert all(asdict(s.summary) == dict(gpa=3.25, cgpa=2.59, local_credit=8, ects=12)
               for s in extraction.document.semesters)
    assert run_transcript_workflow(text).step == "weighting_required"
    for field, expected in (("local_credit", 4), ("ects", 6)):
        decision = run_transcript_workflow(text, gpa_weighting_field=field)
        assert len(decision.courses) == 4
        assert all(c.gpa_credit == expected for c in decision.courses)


def test_semester_gno_is_not_a_conflicting_document_gpa():
    document = extract_official_document("""Cumulative GPA: 2.59
2024-2025 Fall
DNO:2.37 GNO:2.37 TUK:23 TAKTS:30
2024-2025 Spring
DNO:2.5 GNO:2.43 TUK:20 TAKTS:30
2025-2026 Fall
DNO:2.62 GNO:2.59 TUK:25 TAKTS:34
""", [], [])
    assert document.summary.cgpa == 2.59
    assert document.summary.total_local_credit is None
    assert [s.summary.cgpa for s in document.semesters] == [2.37, 2.43, 2.59]
    assert [s.summary.local_credit for s in document.semesters] == [23, 20, 25]


def test_incomplete_mapping_is_rejected_before_weighting_selection():
    text = "CS101 Algorithms 3 5 AA\nCS102 Databases 4 BB"
    with pytest.raises(MappingValidationError) as exc:
        run_transcript_workflow(text, semantic_field_positions={"local_credit": -2, "ects": -1})
    assert exc.value.code == "incomplete_mapping"


def test_legends_do_not_prevent_a_later_explicit_course_table():
    extraction = extract_transcript("""Explanations
PREP 114 Example course 50 - 59 DC 1.5
2024-2025 Spring
Code | Course name | UK | ECTS | Grade
CS101 | Algorithms | 3 | 5 | AA
""")
    assert [(c.code, c.local_credit) for c in extraction.courses] == [("CS101", 3)]
