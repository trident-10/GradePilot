from dataclasses import dataclass

from parsers.generic_analyzer import (
    GenericTranscriptAnalysis,
)


@dataclass
class CreditOption:
    label: str
    field_key: str
    sample_values: list[float]
    score: float
    # Grade-relative column index for generic parsers; None for named fields.
    relative_position: int | None = None


def relative_field_key(relative_position: int) -> str:
    return f"rel:{relative_position}"


def parse_relative_field_key(field_key: str) -> int | None:
    if not field_key.startswith("rel:"):
        return None

    try:
        return int(field_key.removeprefix("rel:"))
    except ValueError as exc:
        raise ValueError(
            f"Invalid relative GPA weighting field: {field_key}"
        ) from exc


def _display_label(label: str | None, index: int) -> str:
    if label is None:
        return f"Kredi Alanı {index}"

    normalized = label.lower()

    if "akts" in normalized or "ects" in normalized:
        return "AKTS / ECTS"

    if (
        "kredi" in normalized
        or "yerel" in normalized
        or normalized == "uk"
        or "credit" in normalized
    ):
        return "Kredi"

    return label


def build_credit_options(
    analysis: GenericTranscriptAnalysis
) -> list[CreditOption]:

    options = []

    for index, candidate in enumerate(
        analysis.credit_candidates,
        start=1
    ):
        options.append(
            CreditOption(
                label=_display_label(candidate.label, index),
                field_key=relative_field_key(
                    candidate.relative_position
                ),
                sample_values=candidate.values[:5],
                score=candidate.score,
                relative_position=candidate.relative_position,
            )
        )

    return options
