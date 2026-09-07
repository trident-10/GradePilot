from __future__ import annotations

from parsers.credit_options import CreditOption, MappingCandidate
from parsers.gpa_weighting import FIELD_ECTS, FIELD_LOCAL_CREDIT
from validation.mapping_validation import MappingValidationError


class InvalidWeightingFieldError(MappingValidationError):
    """Raised when the client sends an unsupported public weighting id."""

    def __init__(self, message: str):
        super().__init__("invalid_weighting_field", message)


def public_option_id(option: CreditOption, index: int) -> str:
    """Map an internal CreditOption to a frontend-safe id."""

    if option.field_key == FIELD_LOCAL_CREDIT:
        return "credit"

    if option.field_key == FIELD_ECTS:
        return "ects"

    label = option.label.lower()

    if label == "kredi":
        return "credit"

    if "akts" in label or "ects" in label:
        return "ects"

    # Avoid exposing relative_position / parser internals.
    return f"field_{index}"


def build_public_option_map(
    options: list[CreditOption] | None,
) -> dict[str, str]:
    """
    Return {public_id: internal_field_key}.

    Deduplicates public ids so collisions become field_N.
    """

    mapping: dict[str, str] = {}
    if not options:
        return mapping

    for index, option in enumerate(options, start=1):
        public_id = public_option_id(option, index)
        if public_id in mapping:
            public_id = f"field_{index}"
        mapping[public_id] = option.field_key

    return mapping


def resolve_weighting_field(
    public_weighting_field: str | None,
    options: list[CreditOption] | None,
) -> str | None:
    """Translate a public API weighting id into an internal field_key."""

    if public_weighting_field is None:
        return None

    normalized = public_weighting_field.strip().lower()
    if not normalized:
        return None

    # Reject raw relative-position style values from clients.
    if normalized.startswith("rel:"):
        raise InvalidWeightingFieldError(
            "Invalid weighting field."
        )

    aliases = {
        "credit": "credit",
        "kredi": "credit",
        "local_credit": "credit",
        "ects": "ects",
        "akts": "ects",
    }
    public_id = aliases.get(normalized, normalized)

    mapping = build_public_option_map(options)
    internal = mapping.get(public_id)

    if internal is None:
        raise InvalidWeightingFieldError(
            "Invalid weighting field for this transcript."
        )

    return internal


def public_mapping_candidate_id(index: int) -> str:
    letter = chr(ord("a") + index - 1) if index <= 26 else str(index)
    return f"column_{letter}"


def build_public_mapping_candidate_map(
    candidates: list[MappingCandidate] | None,
) -> dict[str, int]:
    if not candidates:
        return {}

    return {
        public_mapping_candidate_id(index): candidate.relative_position
        for index, candidate in enumerate(candidates, start=1)
    }


def resolve_semantic_field_positions(
    *,
    local_credit_field: str | None,
    ects_field: str | None,
    candidates: list[MappingCandidate] | None,
) -> dict[str, int] | None:
    """Resolve opaque public column ids to parser-only relative positions."""

    normalized_local = (
        local_credit_field.strip().lower()
        if local_credit_field is not None
        else None
    )
    normalized_ects = (
        ects_field.strip().lower()
        if ects_field is not None
        else None
    )

    if not normalized_local and not normalized_ects:
        return None

    if normalized_local and normalized_local == normalized_ects:
        raise MappingValidationError("duplicate_mapping")

    public_map = build_public_mapping_candidate_map(candidates)
    resolved: dict[str, int] = {}

    for semantic_field, public_id in (
        (FIELD_LOCAL_CREDIT, normalized_local),
        (FIELD_ECTS, normalized_ects),
    ):
        if not public_id:
            continue

        position = public_map.get(public_id)
        if position is None:
            raise MappingValidationError("invalid_mapping")
        resolved[semantic_field] = position

    return resolved
