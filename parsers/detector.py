from dataclasses import dataclass


@dataclass
class TranscriptDetection:
    format_name: str
    confidence: float
    credit_mode: str | None
    requires_credit_selection: bool


def detect_transcript_format(
    text: str
) -> TranscriptDetection:

    normalized_text = text.lower()

    if (
        "çankaya university" in normalized_text
        or "çankaya üniversitesi" in normalized_text
    ):
        # Parser can extract structure accurately, but GPA weighting
        # (local credit vs ECTS) remains a user decision.
        return TranscriptDetection(
            format_name="cankaya",
            confidence=1.0,
            credit_mode=None,
            requires_credit_selection=True,
        )

    return TranscriptDetection(
        format_name="unknown",
        confidence=0.0,
        credit_mode=None,
        requires_credit_selection=True,
    )
