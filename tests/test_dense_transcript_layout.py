"""Synthetic dense tables: narrow gutters, uneven rows and local footers."""
import pdfplumber
import pytest
from fpdf import FPDF

from parsers.document_parser import extract_transcript
from parsers.pdf_layout import extract_page_blocks, extract_page_text
from services.transcript_workflow import run_transcript_workflow
from validation.transcript_validation import validate_transcript


def _dense_pdf(path, credit_label="Donem Kredi"):
    pdf = FPDF(unit="pt", format=(600, 840))
    pdf.add_page()
    pdf.set_font("helvetica", size=6.8)
    pdf.text(38, 40, "Official academic transcript with full width text above the local semester tables")
    expected = []
    for pair in range(4):
        top = 80 + pair * 130
        for lane, term in enumerate(("GUZ", "BAHAR")):
            offset = lane * 269
            pdf.text(39 + offset, top, f"{2 * pair + lane + 1}. DONEM ({term})")
            pdf.text(247 + offset, top, f"{2020 + pair} - {2021 + pair}")
            for x, cell in zip((38, 78, 198, 219, 246, 270),
                               ("KOD", "DERS ADI", "T+U", "KREDI", "AKTS", "HARF")):
                pdf.text(x + offset, top + 14, cell)
            # One table ends while a course in its neighbour continues.
            count = 3 if pair == 2 and lane == 1 else 2
            for row in range(count):
                code = f"CS{pair + 1}{lane}{row}"
                if pair == 2 and lane == 1 and row == 2:
                    code = "TE-I"
                elif pair == 3 and lane == 1 and row == 1:
                    code = "NTE-II"
                expected.append((code, f"{2020 + pair}-{2021 + pair} {'Güz' if lane == 0 else 'Bahar'}"))
                for x, cell in zip((38, 78, 198, 227, 253, 275),
                                   (code, "Programming Languages", "3+2", "3", "5", "BA")):
                    pdf.text(x + offset, top + 27 + 13 * row, cell)
            footer = top + 27 + 13 * count
            pdf.text(39 + offset, footer, f"{credit_label}: {3 * count} | AKTS: {5 * count}")
            pdf.text(201 + offset, footer, "DONEM ORT. (YANO): 3.50")
    pdf.text(38, 640, "Explanation: full width text after the tables must remain in its original reading order")
    path.write_bytes(bytes(pdf.output()))
    return expected


@pytest.mark.parametrize("credit_label", ["Donem Kredi", "D.Kredi"])
def test_dense_parallel_tables_preserve_all_rows_and_semester_footers(tmp_path, monkeypatch, credit_label):
    path = tmp_path / "dense.pdf"
    expected = _dense_pdf(path, credit_label)

    def forbidden(*args, **kwargs):
        raise AssertionError("The page must never be cropped")

    monkeypatch.setattr(pdfplumber.page.Page, "crop", forbidden)
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        blocks = extract_page_blocks(page)
        key = lambda w: (w["text"], w["x0"], w["top"])
        preserved = [w for block in blocks for column in block.columns for line in column for w in line]
        assert sorted(map(key, preserved)) == sorted(map(key, page.dedupe_chars().extract_words(x_tolerance=2, y_tolerance=3)))
        assert len([block for block in blocks if len(block.columns) == 2]) == 4
        text = extract_page_text(page)
    assert "full width text above the local semester tables" in text
    assert "Explanation: full width text after the tables must remain in its original reading order" in text
    extraction = extract_transcript(text)
    assert not validate_transcript(extraction).issues
    assert [(c.code, c.semester) for c in extraction.courses] == expected
    assert all((c.name, c.local_credit, c.ects) == ("Programming Languages", 3, 5) for c in extraction.courses)
    assert len(extraction.document.semesters) == 8
    for semester in extraction.document.semesters:
        count = len(semester.courses)
        assert (semester.summary.gpa, semester.summary.local_credit, semester.summary.ects) == (3.5, 3 * count, 5 * count)
    assert run_transcript_workflow(text).step == "weighting_required"
    selected = run_transcript_workflow(text, gpa_weighting_field="local_credit")
    assert selected.step == "review_required"
    assert len(selected.courses) == len(expected)


@pytest.mark.parametrize("code", ["TE-I", "TE-II", "TE-III", "NTE-I", "NTE-II"])
@pytest.mark.parametrize("separator", [" ", " | "])
def test_elective_identifiers_and_abbreviated_grade_header(code, separator):
    text = separator.join(("KOD", "DERS ADI", "T+U", "KREDI", "AKTS", "HARF")) + "\n"
    text += separator.join((code, "Technical Elective", "1+4", "3", "5", "AA"))
    decision = run_transcript_workflow(text, gpa_weighting_field="local_credit")
    assert [(c.code, c.name, c.local_credit, c.ects) for c in decision.courses] == [
        (code, "Technical Elective", 3, 5)
    ]


def test_unknown_identifiers_without_schema_do_not_create_courses():
    extraction = extract_transcript("NTE-I Technical Elective 3 5 AA")
    assert extraction.courses == []
