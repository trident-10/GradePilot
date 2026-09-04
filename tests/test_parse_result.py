from models.course import Course
from models.parse_result import ParseResult


def test_parse_result_model():

    course = Course(
        code="CENG101",
        name="Programming",
        gpa_credit=4,
        grade="AA",
        semester="Test",
    )

    result = ParseResult(
        courses=[course],
        format_name="cankaya",
        confidence=1.0,
        requires_user_confirmation=False,
        requires_credit_selection=False,
        warnings=[],
    )

    assert result.courses[0].code == "CENG101"
    assert result.format_name == "cankaya"
    assert result.confidence == 1.0
    assert result.requires_user_confirmation is False
    assert result.requires_credit_selection is False
    assert result.warnings == []
    assert result.credit_options is None
