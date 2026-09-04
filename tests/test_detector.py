from parsers.detector import detect_transcript_format


def test_detect_cankaya_format():

    text = """
    Çankaya University
    Official Transcript
    """

    result = detect_transcript_format(text)

    assert result.format_name == "cankaya"
    assert result.confidence == 1.0
    assert result.credit_mode is None
    assert result.requires_credit_selection is True


def test_detect_cankaya_turkish_name():

    text = "Çankaya Üniversitesi Transkript"

    result = detect_transcript_format(text)

    assert result.format_name == "cankaya"
    assert result.credit_mode is None
    assert result.requires_credit_selection is True


def test_detect_unknown_format():

    text = """
    Some Other University
    Grade Report
    """

    result = detect_transcript_format(text)

    assert result.format_name == "unknown"
    assert result.confidence == 0.0
    assert result.credit_mode is None
    assert result.requires_credit_selection is True
