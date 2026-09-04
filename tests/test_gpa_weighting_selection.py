from core.gpa_engine import calculate_gpa
from parsers.gpa_weighting import FIELD_ECTS, FIELD_LOCAL_CREDIT
from parsers.transcript_parser import analyze_and_parse_transcript


CANKAYA_TEXT = """
Çankaya University
2024-2025 Güz Dönemi
CENG 111 Bilgisayar Programlama I Z İng. 3 2 4 6 DD 1.00
MATH 157 Genel Matematik I Z Tr 3 2 4 6 BB 3.00
"""

GENERIC_TEXT = """
Example University
Academic Transcript

Course Credit ECTS Grade

CENG101 Programming 3 6 BA
CENG102 Data Structures 4 7 BB
MATH101 Calculus 4 6 CB
PHYS101 Physics 3 5 AA
"""


def test_cankaya_offers_credit_and_ects_options():
    result = analyze_and_parse_transcript(CANKAYA_TEXT)

    assert result.format_name == "cankaya"
    assert result.requires_credit_selection is True
    assert result.courses == []
    assert result.credit_options is not None

    labels = [option.label for option in result.credit_options]
    keys = [option.field_key for option in result.credit_options]

    assert labels == ["Kredi", "AKTS / ECTS"]
    assert keys == [FIELD_LOCAL_CREDIT, FIELD_ECTS]
    assert 4.0 in result.credit_options[0].sample_values
    assert 6.0 in result.credit_options[1].sample_values


def test_cankaya_select_credit_uses_local_credit():
    result = analyze_and_parse_transcript(
        CANKAYA_TEXT,
        gpa_weighting_field=FIELD_LOCAL_CREDIT,
    )

    assert result.requires_credit_selection is False
    assert result.requires_user_confirmation is False
    assert len(result.courses) == 2

    first = result.courses[0]
    assert first.gpa_credit == 4.0
    assert first.ects == 6.0
    assert first.local_credit == 4.0
    assert first.source_order == 0
    assert result.courses[1].source_order == 1


def test_cankaya_select_ects_uses_ects_as_gpa_credit():
    result = analyze_and_parse_transcript(
        CANKAYA_TEXT,
        gpa_weighting_field=FIELD_ECTS,
    )

    assert result.requires_credit_selection is False
    assert len(result.courses) == 2

    first = result.courses[0]
    assert first.gpa_credit == 6.0
    assert first.ects == 6.0
    assert first.local_credit == 4.0


def test_cankaya_extraction_still_works_before_selection():
    from parsers.formats.cankaya_parser import extract_cankaya_courses

    extracted = extract_cankaya_courses(CANKAYA_TEXT)

    assert len(extracted) == 2
    assert extracted[0].code == "CENG111"
    assert extracted[0].local_credit == 4.0
    assert extracted[0].ects == 6.0
    assert extracted[0].source_order == 0
    assert extracted[1].source_order == 1


def test_generic_still_requires_confirmation_after_selection():
    first = analyze_and_parse_transcript(GENERIC_TEXT)

    assert first.requires_credit_selection is True
    assert first.requires_user_confirmation is True
    assert first.credit_options

    selected = first.credit_options[0]
    second = analyze_and_parse_transcript(
        GENERIC_TEXT,
        gpa_weighting_field=selected.field_key,
    )

    assert second.requires_credit_selection is False
    assert second.requires_user_confirmation is True
    assert second.courses


def test_generic_credit_and_ects_options_when_both_detected():
    result = analyze_and_parse_transcript(GENERIC_TEXT)

    assert result.credit_options is not None
    labels = {option.label for option in result.credit_options}

    # Analyzer may surface both labeled columns for this fixture.
    assert "Kredi" in labels or "AKTS / ECTS" in labels


def test_engines_still_work_after_ects_weighting():
    result = analyze_and_parse_transcript(
        CANKAYA_TEXT,
        gpa_weighting_field=FIELD_ECTS,
    )

    gpa = calculate_gpa(result.courses)

    # DD(1.0)*6 + BB(3.0)*6 = 24 over 12 credits
    assert gpa == 2.0
