"""Anonymous regressions for numbered terms, exemption grades and summaries."""
import pytest
from fastapi.testclient import TestClient
from fpdf import FPDF

from api.main import create_app
from core.gpa_engine import calculate_gpa
from parsers.document_parser import extract_transcript
from parsers.headers import is_course_identifier
from parsers.transcript_parser import keep_latest_attempts
from services.transcript_workflow import run_transcript_workflow
from validation.transcript_validation import validate_transcript


HEADER = "Code\tCourse name\tStatus\tECTS\tGrade\tPoints\tComment"


@pytest.mark.parametrize("value", ["2.", "8.", "3.06", "240.0"])
def test_summary_numbers_and_list_markers_are_not_course_identifiers(value):
    assert not is_course_identifier(value)


@pytest.mark.parametrize("status", ["MUF", "G"])
def test_non_gpa_status_is_read_from_the_grade_column(status):
    text = f"2024-2025 Fall\n{HEADER}\nCS101\tAlgorithms\tZ\t5\tBA\t3.5\tPassed\n"
    text += f"CS102\tInternship\tZ\t4\t{status}\t-\tExcluded"
    decision = run_transcript_workflow(text, gpa_weighting_field="ects")
    assert [c.code for c in decision.courses] == ["CS101"]
    assert [(i.code, i.count) for i in decision.issues] == [("excluded_courses", 1)]


def test_unknown_grade_cannot_be_hidden_by_a_status_in_another_column():
    text = f"{HEADER}\nCS101\tAlgorithms\tZ\t5\tUNKNOWN\t3.5\tG"
    assert validate_transcript(extract_transcript(text)).errors[0].code == "unreadable_course"


def test_numbered_semesters_and_summary_are_not_extra_courses():
    text = f"""1. YARIYIL (GUZ DONEMI)\t2024 - 2025 EGITIM-OGRETIM YILI
{HEADER}
CS101\tAlgorithms\tZ\t5\tFF\t0.0\tFailed
2. YARIYIL (BAHAR DONEMI)\t2024 - 2025 EGITIM-OGRETIM YILI
{HEADER}
CS101\tAlgorithms repeated\tZ\t5\tAA\t4.0\tPassed
GENEL AKADEMIK DEGERLENDIRME VE MEZUNIYET OZETI
GENEL AGIRLIKLI NOT ORTALAMASI
3.06 (Dortluk Sistem Uzerinden)
(GANO):
"""
    decision = run_transcript_workflow(text, gpa_weighting_field="ects")
    assert len(decision.extraction.rows) == 2
    assert [s.label for s in decision.extraction.document.semesters] == ["2024-2025 Güz", "2024-2025 Bahar"]
    assert decision.extraction.document.summary.cgpa == 3.06
    # Official GPA is independent of the GPA computed from the latest attempts.
    assert calculate_gpa(keep_latest_attempts(list(reversed(decision.courses)))) == 4.0


def test_staggered_semester_summaries_and_graduation_totals_keep_their_scope():
    text = """2024-2025 Fall
Donem Not Ort. (DNO):\tGenel Not Ort. (GNO):
Donem AKTS Toplami: 30 (Degerlendirilen: 28)
1.82\t1.82
2024-2025 Spring
Donem Kredisi: 21.0 | AKTS: 30\tDONEM NOT ORTALAMASI (YANO): 1.95 | GENEL NOT ORTALAMASI (GANO): 2.05
MEZUNIYET TESCIL VE GENEL AKADEMIK BASARI OZETI
Kayitli Toplam Ders Sayisi:\t49 Ders (3 Tekrar Dahil)\tKarar Tarihi:\t05.07.2024
Tamamlanan Ulusal Kredi:\t149.0 Kredi\tKarar No:\t2024/28-C
Kazanilan Toplam AKTS:\t240 AKTS\tDerece:\tHONOURS
GANO (CGPA): 3.23 / 4.00
"""
    doc = extract_transcript(text).document
    assert (doc.summary.cgpa, doc.summary.total_local_credit, doc.summary.total_ects, doc.summary.total_course_count) == (3.23, 149, 240, 49)
    assert [(s.summary.gpa, s.summary.cgpa, s.summary.ects) for s in doc.semesters] == [(1.82, 1.82, 30), (1.95, 2.05, 30)]
    assert doc.semesters[1].summary.local_credit == 21


def test_pending_gpa_labels_do_not_cross_course_rows():
    text = f"2024-2025 Fall\n{HEADER}\nDonem Not Ort. (DNO):\tGenel Not Ort. (GNO):\n"
    text += "CS101\tAlgorithms\tZ\t5\tBA\t3.5\tPassed\n1.82\t1.82"
    summary = extract_transcript(text).document.semesters[0].summary
    assert summary.gpa is None and summary.cgpa is None


@pytest.mark.parametrize("local_credit", [False, True])
def test_pdf_upload_reaches_review_with_numbered_terms_and_non_gpa_rows(local_credit):
    pdf = FPDF(unit="pt", format=(700, 850))
    pdf.add_page()
    pdf.set_font("helvetica", size=8)
    xs = [20, 100, 300, 360, 425, 490, 550]
    if local_credit:
        xs = [20, 100, 300, 360, 410, 460, 515, 570]
    for term, top in [("1. YARIYIL (GUZ DONEMI)", 40), ("2. YARIYIL (BAHAR DONEMI)", 180)]:
        pdf.text(20, top, term)
        pdf.text(390, top, "2024 - 2025 EGITIM-OGRETIM YILI")
        columns = ["Code", "Course name", "Status", "ECTS", "Grade", "Points", "Comment"]
        if local_credit:
            columns.insert(4, "Credit")
        for x, value in zip(xs, columns):
            pdf.text(x, top + 20, value)
        for i, (code, grade) in enumerate([("CS101", "BA"), ("LANG101", "MUF"), ("STAJ101", "G")]):
            values = [code, "Example course", "Z", "5", grade, "3.5" if grade == "BA" else "-", "Result"]
            if local_credit:
                values.insert(4, "3")
            for x, value in zip(xs, values):
                pdf.text(x, top + 40 + 15 * i, value)
    pdf.text(20, 310, "GENEL AKADEMIK DEGERLENDIRME VE MEZUNIYET OZETI")
    pdf.text(20, 330, "GENEL AGIRLIKLI NOT ORTALAMASI")
    pdf.text(20, 345, "3.06 (Dortluk Sistem Uzerinden)")
    data = bytes(pdf.output())
    with TestClient(create_app()) as client:
        for form in ({}, {"weighting_field": "credit" if local_credit else "ects"}):
            response = client.post("/api/transcripts/analyze", files={"file": ("anonymous.pdf", data, "application/pdf")}, data=form)
            assert response.status_code == 200, response.text
            body = response.json()
            assert len(body["semesters"]) == 2
            assert body["official_summary"]["cgpa"] == 3.06
            if form:
                assert body["status"] == "confirmation"
                assert len(body["courses"]) == 2
                assert all(c["gpa_credit"] == (3 if local_credit else 5) for c in body["courses"])
            else:
                assert body["status"] == "credit_selection"
                assert {o["id"] for o in body["credit_options"]} == ({"credit", "ects"} if local_credit else {"ects"})
