import pytest

from core.gpa_engine import calculate_gpa
from parsers.gpa_weighting import FIELD_ECTS, FIELD_LOCAL_CREDIT
from parsers.transcript_parser import (
    TranscriptStructureError,
    analyze_and_parse_transcript,
)


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


@pytest.mark.parametrize(
    "header",
    [
        "Ders Kredi AKTS Not",
        "Course Credit ECTS Grade",
    ],
)
def test_explicit_credit_and_ects_headers_are_semantic(header):
    text = f"""
Example University
{header}
CENG101 Programming 3 6 BA
CENG102 Data Structures 4 7 BB
"""

    result = analyze_and_parse_transcript(text)

    assert result.requires_manual_mapping is False
    assert result.requires_credit_selection is True
    assert result.credit_options is not None
    assert [option.field_key for option in result.credit_options] == [
        FIELD_LOCAL_CREDIT,
        FIELD_ECTS,
    ]
    assert all(option.confidence == "high" for option in result.credit_options)


def test_ambiguous_numeric_columns_require_manual_mapping():
    text = """
Example University
Course Value One Value Two Grade
CENG101 Programming 3 6 BA
CENG102 Data Structures 4 7 BB
"""

    result = analyze_and_parse_transcript(text)

    assert result.requires_manual_mapping is True
    assert result.requires_credit_selection is False
    assert result.courses == []
    assert result.mapping_candidates is not None
    assert [candidate.label for candidate in result.mapping_candidates] == [
        "Sütun A",
        "Sütun B",
    ]
    assert all(
        candidate.confidence == "low"
        for candidate in result.mapping_candidates
    )
    assert "Kredi Alanı" not in str(result)


def test_nearby_multiline_headers_are_medium_confidence():
    text = """
Example University
Course Credit ECTS
Letter Grade
CENG101 Programming 3 6 BA
CENG102 Data Structures 4 7 BB
"""

    result = analyze_and_parse_transcript(text)

    assert result.credit_options is not None
    assert [option.field_key for option in result.credit_options] == [
        FIELD_LOCAL_CREDIT,
        FIELD_ECTS,
    ]
    assert all(option.confidence == "medium" for option in result.credit_options)


def test_split_course_number_is_not_a_manual_mapping_candidate():
    text = """
Course Value One Value Two Grade
CENG 101 Programming 3 6 BA
CENG 102 Data Structures 4 7 BB
"""

    result = analyze_and_parse_transcript(text)

    assert result.mapping_candidates is not None
    assert len(result.mapping_candidates) == 2
    assert result.mapping_candidates[0].sample_values == [3.0, 4.0]
    assert result.mapping_candidates[1].sample_values == [6.0, 7.0]


def test_readable_text_without_course_structure_is_not_manual_mapping():
    with pytest.raises(TranscriptStructureError, match="ders yapısı"):
        analyze_and_parse_transcript(
            "Example University\nAcademic Transcript\nTotal Credits 3 6 AA"
        )


def test_manual_mapping_normalizes_both_semantic_fields():
    text = """
Example University
Course Value One Value Two Grade
CENG101 Programming 3 6 BA
CENG102 Data Structures 4 7 BB
"""
    preview = analyze_and_parse_transcript(text)
    assert preview.mapping_candidates is not None
    local_candidate, ects_candidate = preview.mapping_candidates
    mapping = {
        FIELD_LOCAL_CREDIT: local_candidate.relative_position,
        FIELD_ECTS: ects_candidate.relative_position,
    }

    result = analyze_and_parse_transcript(
        text,
        gpa_weighting_field=FIELD_LOCAL_CREDIT,
        semantic_field_positions=mapping,
    )

    assert result.requires_manual_mapping is False
    assert result.requires_credit_selection is False
    assert len(result.courses) == 2
    assert result.courses[0].gpa_credit == 3.0
    assert result.courses[0].local_credit == 3.0
    assert result.courses[0].ects == 6.0


def test_same_manual_column_cannot_fill_both_semantic_roles():
    text = """
Course Value One Value Two Grade
CENG101 Programming 3 6 BA
CENG102 Data Structures 4 7 BB
"""

    with pytest.raises(ValueError, match="same numeric column"):
        analyze_and_parse_transcript(
            text,
            gpa_weighting_field=FIELD_LOCAL_CREDIT,
            semantic_field_positions={
                FIELD_LOCAL_CREDIT: -1,
                FIELD_ECTS: -1,
            },
        )


def test_only_local_credit_is_supported():
    text = """
Course Credit Grade
CENG101 Programming 3 BA
CENG102 Data Structures 4 BB
"""
    preview = analyze_and_parse_transcript(text)

    assert [option.field_key for option in preview.credit_options or []] == [
        FIELD_LOCAL_CREDIT
    ]

    result = analyze_and_parse_transcript(
        text,
        gpa_weighting_field=FIELD_LOCAL_CREDIT,
    )
    assert result.courses[0].local_credit == 3.0
    assert result.courses[0].ects is None
    assert result.courses[0].gpa_credit == 3.0


def test_only_ects_is_supported():
    text = """
Course ECTS Letter Grade
CENG101 Programming 6 BA
CENG102 Data Structures 7 BB
"""
    preview = analyze_and_parse_transcript(text)

    assert [option.field_key for option in preview.credit_options or []] == [
        FIELD_ECTS
    ]

    result = analyze_and_parse_transcript(
        text,
        gpa_weighting_field=FIELD_ECTS,
    )
    assert result.courses[0].local_credit is None
    assert result.courses[0].ects == 6.0
    assert result.courses[0].gpa_credit == 6.0
