from dataclasses import dataclass
from parsers.semantic_fields import DetectionConfidence


@dataclass
class CreditOption:
    label: str
    field_key: str
    sample_values: list[float]
    score: float
    confidence: DetectionConfidence = "high"
    # Grade-relative column index for generic parsers; None for named fields.
    relative_position: int | None = None


@dataclass
class MappingCandidate:
    label: str
    field_key: str
    sample_values: list[float]
    confidence: DetectionConfidence
    relative_position: int


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


