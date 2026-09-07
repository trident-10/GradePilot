from dataclasses import dataclass
from parsers.text_normalization import fold


@dataclass
class TranscriptDetection:
    format_name: str
    confidence: float
    credit_mode: str | None
    requires_credit_selection: bool


def detect_transcript_format(
    text: str
) -> TranscriptDetection:

    normalized_text = fold(text)

    if (
        "cankaya university" in normalized_text
        or "cankaya universitesi" in normalized_text
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
