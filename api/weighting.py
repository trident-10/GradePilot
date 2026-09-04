from __future__ import annotations

from parsers.credit_options import CreditOption
from parsers.gpa_weighting import FIELD_ECTS, FIELD_LOCAL_CREDIT


class InvalidWeightingFieldError(ValueError):
    """Raised when the client sends an unsupported public weighting id."""


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
