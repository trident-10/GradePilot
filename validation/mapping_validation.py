"""Validation of caller choices, separate from defects in the document."""


class MappingValidationError(ValueError):
    MESSAGES = {
        "empty_mapping": "At least one credit mapping is required.",
        "unsupported_mapping": "Unsupported semantic credit field.",
        "duplicate_mapping": "The same numeric column cannot be assigned to both local credit and ECTS.",
        "invalid_mapping": "Invalid numeric column mapping.",
        "mapping_not_applicable": "Manual mapping is not valid for this transcript.",
        "incomplete_mapping": "The selected numeric column is not available for every course.",
        "invalid_weighting_field": "Invalid weighting field for this transcript.",
    }

    def __init__(self, code: str, message: str | None = None):
        self.code = code
        super().__init__(message or self.MESSAGES[code])


def validate_mapping(positions: dict[str, int], candidates: set[int]) -> None:
    if not isinstance(positions, dict):
        raise MappingValidationError("invalid_mapping")
    if not positions:
        raise MappingValidationError("empty_mapping")
    if not set(positions).issubset({"local_credit", "ects"}):
        raise MappingValidationError("unsupported_mapping")
    if any(type(position) is not int for position in positions.values()):
        raise MappingValidationError("invalid_mapping")
    if len(positions) != len(set(positions.values())):
        raise MappingValidationError("duplicate_mapping")
    if any(position not in candidates for position in positions.values()):
        raise MappingValidationError("invalid_mapping")
