"""Anonymous regressions for full-width UK/AKTS tables and safe fallbacks."""
import io

import pdfplumber
import pytest
from fastapi.testclient import TestClient
from fpdf import FPDF

from api.main import create_app
from core.gpa_engine import calculate_gpa
from parsers.document_parser import extract_transcript
from parsers.pdf_layout import extract_page_blocks, extract_page_text
from parsers.transcript_parser import keep_latest_attempts
from services.transcript_workflow import analyze_and_parse_transcript, run_transcript_workflow
from validation.mapping_validation import MappingValidationError


@pytest.mark.parametrize("tail", ["Açıklama", "Explanation", "Total", "Comment"])
@pytest.mark.parametrize("separator", [" ", " | ", "\t"])
def test_header_boundary_words_do_not_discard_credit_schema(tail, separator):
    header = separator.join(["Ders Kodu", "Ders Adı", "D.Dili", "T", "U", "UK",
                             "AKTS", "Not", "Katsayı", "Puan", tail])
    row = separator.join(["CS101", "Programming", "Ing.", "3", "2", "4",
                          "6", "BA", "3.5", "14", "G"])
    preview = analyze_and_parse_transcript(header + "\n" + row)
    assert preview.requires_credit_selection
    assert not preview.requires_manual_mapping
    assert {o.field_key for o in preview.credit_options} == {"local_credit", "ects"}
    selected = run_transcript_workflow(header + "\n" + row, gpa_weighting_field="local_credit")
    assert [(c.name, c.local_credit, c.ects, c.grade) for c in selected.courses] == [
        ("Programming", 4, 6, "BA")
    ]
    assert {c.relative_position for c in selected.extraction.analysis.credit_candidates} == {-2, -1}


@pytest.mark.parametrize("label", ["Kredi", "Credit", "Credits", "Local Credit", "Course Credit", "CR", "UK"])
def test_credit_aliases_preserve_the_printed_label(label):
    extraction = extract_transcript(f"Code | Course Name | {label} | Grade\nCS101 | Programming | 3 | BA")
    assert len(extraction.analysis.credit_candidates) == 1
    candidate = extraction.analysis.credit_candidates[0]
    assert (candidate.semantic_field, candidate.confidence, candidate.header_label) == ("local_credit", "high", label)


@pytest.mark.parametrize("field, header", [("local_credit", "UK"), ("ects", "ECTS")])
def test_single_credit_system_needs_no_manual_column_mapping(field, header):
    text = f"Code | Course Name | T | U | {header} | Grade | Coefficient | Points\nCS101 | Programming | 3 | 0 | 4 | BA | 3.5 | 14"
    preview = analyze_and_parse_transcript(text)
    assert not preview.requires_manual_mapping
    assert [o.field_key for o in preview.credit_options] == [field]
    selected = run_transcript_workflow(text, gpa_weighting_field=field)
    assert selected.courses[0].gpa_credit == 4


def test_named_unknown_columns_keep_labels_and_exclude_hours_and_points():
    text = """Code | Course Name | T | U | Value A | Value B | Grade | Coefficient | Points
CS101 | Programming | 3 | 0 | 3 | 6 | BA | 3.5 | 10.5
CS102 | Algorithms | 3 | 2 | 4 | 7 | BB | 3 | 12
"""
    result = analyze_and_parse_transcript(text)
    assert result.requires_manual_mapping
    assert [(c.label, c.relative_position) for c in result.mapping_candidates] == [("Value A", -2), ("Value B", -1)]
    assert all(c.confidence == "low" for c in result.mapping_candidates)
    mapped = run_transcript_workflow(text, semantic_field_positions={"local_credit": -2}, gpa_weighting_field="local_credit")
    assert [c.gpa_credit for c in mapped.courses] == [3, 4]
    with pytest.raises(MappingValidationError):
        run_transcript_workflow(text, semantic_field_positions={"local_credit": 1})
    with pytest.raises(MappingValidationError):
        run_transcript_workflow(text, semantic_field_positions={"local_credit": -2, "ects": -2})


def test_unknown_headers_without_cell_boundaries_never_guess_credits():
    result = analyze_and_parse_transcript("Course Credit ECTS Unknown Grade\nCS101 Programming 3 6 85 BA")
    assert result.requires_manual_mapping
    assert all(c.confidence == "low" for c in result.mapping_candidates)
    assert all(c.label.startswith("Sütun ") for c in result.mapping_candidates)


def _bilingual_pdf(official_gpa="3.43"):
    """No names, student identifiers or contents from the user's document."""
    pdf = FPDF(unit="pt", format=(600, 840))
    pdf.add_page()
    pdf.set_font("helvetica", size=8)
    positions = (30, 88, 300, 339, 363, 389, 421, 454, 478, 516, 550)
    header = ("Ders Kodu", "Ders Adi", "D.Dili", "T", "U", "UK", "AKTS", "Not", "Katsayi", "Puan", "Aciklama")
    terms = [
        ("GUZ", "Fall", [("CS101", "Programming", "3", "0", "3", "6", "BA", "3.5", "10.5", "G"),
                          ("CS102", "Algorithms", "3", "2", "4", "7", "BB", "3", "12", "G")], 7, 13, "3.21"),
        ("BAHAR", "Spring", [("CS101", "Programming", "3", "0", "3", "6", "AA", "4", "12", "TKR G")], 3, 6, "4.00"),
    ]
    for term_index, (turkish, english, courses, credit, ects, gpa) in enumerate(terms):
        top = 65 + term_index * 130
        pdf.text(30, top, f"2024-2025 {turkish} DONEMI ({term_index + 1}. YARIYIL)")
        pdf.text(450, top, f"2024-2025 {english} Term")
        for x, label in zip(positions, header):
            pdf.text(x, top + 16, label)
        for row_index, (code, name, *cells) in enumerate(courses):
            for x, cell in zip(positions, (code, name, "Ing.", *cells)):
                pdf.text(x, top + 32 + row_index * 16, cell)
        pdf.text(30, top + 80, f"Donem Ulusal Kredisi (TUK): {credit} | Donem AKTS (TAKTS): {ects}")
        pdf.text(345, top + 80, f"DNO: {gpa} | GNO: {gpa if term_index == 0 else official_gpa}")
    pdf.text(30, 355, "Tamamlanan Toplam Ulusal Kredi: 7 Kredi")
    pdf.text(30, 370, "Kazanilan Toplam AKTS: 13 AKTS")
    pdf.text(30, 385, f"Genel Not Ortalamasi (GNO / CGPA): {official_gpa} / 4.00")
    return bytes(pdf.output())


def test_bilingual_full_width_table_keeps_semesters_and_all_words():
    with pdfplumber.open(io.BytesIO(_bilingual_pdf())) as pdf:
        page = pdf.pages[0]
        blocks = extract_page_blocks(page)
        key = lambda w: (w["text"], w["x0"], w["top"])
        original = page.dedupe_chars().extract_words(x_tolerance=2, y_tolerance=3)
        preserved = [w for b in blocks for col in b.columns for line in col for w in line]
        assert sorted(map(key, original)) == sorted(map(key, preserved))
        text = extract_page_text(page)
    result = run_transcript_workflow(text, gpa_weighting_field="local_credit")
    assert [c.semester for c in result.courses] == ["2024-2025 Güz", "2024-2025 Güz", "2024-2025 Bahar"]
    assert [(c.local_credit, c.ects) for c in result.courses] == [(3, 6), (4, 7), (3, 6)]
    assert not result.issues
    document = result.extraction.document
    assert document.summary.cgpa == 3.43
    assert document.summary.total_local_credit == 7
    assert [s.summary.local_credit for s in document.semesters] == [7, 3]
    assert [s.summary.ects for s in document.semesters] == [13, 6]
    assert [s.summary.cgpa for s in document.semesters] == [3.21, 3.43]


def test_same_language_same_term_parallel_tables_are_not_joined():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=9)
    for x, code in [(10, "CS101"), (110, "CS102")]:
        pdf.text(x, 20, "2024-2025 Fall")
        pdf.text(x, 26, "Course Credit ECTS Grade")
        pdf.text(x, 32, f"{code} Programming 3 6 BA")
    with pdfplumber.open(io.BytesIO(bytes(pdf.output()))) as doc:
        text = extract_page_text(doc.pages[0])
    assert "[[TABLE_NEXT]]" in text
    result = run_transcript_workflow(text, gpa_weighting_field="local_credit")
    assert len(result.courses) == 2
    assert all(c.semester == "2024-2025 Güz" for c in result.courses)


@pytest.mark.parametrize("official, mismatch", [("3.43", False), ("3.17", True)])
def test_api_skips_anonymous_mapping_and_reports_real_gpa_mismatch(official, mismatch):
    data = _bilingual_pdf(official)
    with TestClient(create_app()) as client:
        preview = client.post("/api/transcripts/analyze", files={"file": ("anonymous.pdf", data, "application/pdf")})
        assert preview.status_code == 200, preview.text
        assert preview.json()["status"] == "credit_selection"
        assert {o["id"] for o in preview.json()["credit_options"]} == {"credit", "ects"}
        assert preview.json()["mapping_candidates"] == []
        response = client.post("/api/transcripts/analyze", files={"file": ("anonymous.pdf", data, "application/pdf")},
                               data={"weighting_field": "credit"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "confirmation"
    assert len(body["courses"]) == 3
    assert len(body["semesters"]) == 2
    assert body["official_summary"]["cgpa"] == float(official)
    assert any("genel ortalama uyuşmuyor" in w for w in body["warnings"]) == mismatch
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        selected = run_transcript_workflow(extract_page_text(pdf.pages[0]), gpa_weighting_field="local_credit")
    assert calculate_gpa(keep_latest_attempts(selected.courses)) == pytest.approx(24 / 7)


def test_no_printed_cgpa_does_not_invent_a_mismatch():
    result = run_transcript_workflow("Course Credit ECTS Grade\nCS101 Programming 3 6 BA", gpa_weighting_field="local_credit")
    assert not any(i.code == "official_gpa_mismatch" for i in result.issues)


@pytest.mark.parametrize("system, field, index, credits", [
    ("credit", "local_credit_field", 0, [3, 4]),
    ("ects", "ects_field", 1, [6, 7]),
])
def test_one_column_and_system_complete_mapping_in_one_request(system, field, index, credits):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=8)
    for y, line in enumerate([
        "Code | Course Name | T | U | Value A | Value B | Grade | Coefficient | Points",
        "CS101 | Programming | 3 | 0 | 3 | 6 | BA | 3.5 | 10.5",
        "CS102 | Algorithms | 3 | 2 | 4 | 7 | BB | 3 | 12",
    ]):
        pdf.text(10, 20 + y * 6, line)
    data = bytes(pdf.output())
    with TestClient(create_app()) as client:
        upload = {"file": ("anonymous.pdf", data, "application/pdf")}
        preview = client.post("/api/transcripts/analyze", files=upload)
        assert preview.status_code == 200
        body = preview.json()
        assert body["status"] == "manual_mapping"
        candidates = body["mapping_candidates"]
        assert [c["label"] for c in candidates] == ["Value A", "Value B"]
        assert all(set(c) == {"id", "label", "sample_values", "confidence"} for c in candidates)
        chosen = candidates[index]["id"]
        response = client.post("/api/transcripts/analyze", files=upload,
                               data={field: chosen, "weighting_field": system})
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "confirmation"
        assert [c["gpa_credit"] for c in response.json()["courses"]] == credits
        duplicate = client.post("/api/transcripts/analyze", files=upload,
                                data={"local_credit_field": chosen, "ects_field": chosen})
        assert duplicate.status_code == 400
        assert duplicate.json()["code"] == "duplicate_mapping"
