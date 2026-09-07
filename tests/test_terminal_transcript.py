"""Synthetic terminal-style tables, without private transcript fixtures."""
from io import BytesIO

import pdfplumber
import pytest
from fpdf import FPDF

from parsers.document_parser import extract_transcript
from parsers.pdf_layout import extract_page_text
from services.transcript_workflow import run_transcript_workflow
from validation.transcript_validation import validate_transcript


HEADER = "DERS KOD\tDERSIN ADI\tT+U+L\tKREDI\tAKTS\tNOT\tKATSAYI DURUM\tD.TUR"


@pytest.mark.parametrize("field, weight", [("local_credit", 5), ("ects", 8)])
def test_wrapped_numeric_totals_do_not_become_courses_or_reset_the_schema(field, weight):
    text = f"""{HEADER}
>>> 2024-2025 GUZ YARIYILI (1. DONEM)
CS101\tPLANNING STUDIO I\t2+6+0\t5.0\t8\tBA\t3.50 GECTI\tZ
ENG101\tENGLISH I\t3+0+0\t3.0\t3\tS\t- MUAF\tZ
18.0
30 (Deg: DNO: 2.43 | GNO: 2.43 | KAZANILAN
DONEM TOPLAMI / ORTALAMALARI:\t(Deg:
27)\tAKTS: 22
15.0)
>>> 2024-2025 BAHAR YARIYILI (2. DONEM)
CS102\tPLANNING STUDIO II\t2+6+0\t5.0\t8\tBB\t3.00 GECTI\tZ
STJ101\tINTERNSHIP\t0+0+0\t0.0\t4\tP\t- BASAR\tZ
"""
    decision = run_transcript_workflow(text, gpa_weighting_field=field)
    assert len(decision.extraction.rows) == 4
    assert [(c.name, c.gpa_credit) for c in decision.courses] == [("PLANNING STUDIO I", weight), ("PLANNING STUDIO II", weight)]
    assert [c.semester for c in decision.courses] == ["2024-2025 Güz", "2024-2025 Bahar"]
    assert [(i.code, i.count) for i in decision.issues] == [("excluded_courses", 2)]


def test_numeric_course_ids_with_summary_words_in_the_name_are_preserved():
    text = f"{HEADER}\n123456\tComputing GPA: Statistics\t3+0+0\t3.0\t5\tAA\t4.00 GECTI\tZ"
    extraction = extract_transcript(text)
    assert not validate_transcript(extraction).errors
    assert extraction.courses[0].code == "123456"


@pytest.mark.parametrize("overlap", [False, True])
def test_wrapped_summary_amount_is_joined_only_in_an_empty_aligned_cell(overlap):
    pdf = FPDF(unit="pt", format=(600, 400))
    pdf.add_page()
    pdf.set_font("courier", size=7)
    pdf.text(30, 30, "MEZUNIYET KAYIT VE AKADEMIK DERECELENDIRME RAPORU")
    pdf.text(30, 50, "TOPLAM DERS SAYISI:")
    pdf.text(170, 50, "48 DERS (3 TEKRAR)")
    pdf.text(170, 66, "144.0 KREDI (DEGERLENDIRILEN:")
    pdf.text(30, 70, "KREDI TOPLAMI (YEREL):")
    pdf.text(170, 74, "138.0)")
    pdf.text(300, 70, "KURUL KARARI:")
    pdf.text(425, 70, "2023/52-A")
    if overlap:
        pdf.text(180, 70, "unrelated value")
    pdf.text(30, 90, "TOPLAM AKTS:")
    pdf.text(170, 90, "240 AKTS")
    pdf.text(30, 110, "GANO (CGPA): 3.31 / 4.00 - HIGH HONOURS")
    with pdfplumber.open(BytesIO(bytes(pdf.output()))) as doc:
        text = extract_page_text(doc.pages[0])
    summary = extract_transcript(text).document.summary
    assert summary.total_local_credit == (None if overlap else 144)
    assert (summary.cgpa, summary.total_ects, summary.total_course_count) == (3.31, 240, 48)
    assert "2023/52-A" in text


def test_summary_does_not_hide_an_unreadable_course():
    text = f"{HEADER}\nCS101\tPLANNING STUDIO\t2+6+0\t5.0\t8\t?\t? GECTI\tZ"
    assert validate_transcript(extract_transcript(text)).errors[0].code == "unreadable_course"
