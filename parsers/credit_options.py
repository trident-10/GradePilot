"""Compatibility exports. Presentation builders live in services."""
from models.credit_fields import CreditOption, MappingCandidate, parse_relative_field_key, relative_field_key


def build_credit_options(analysis):
    from services.transcript_presentation import build_credit_options as build
    return build(analysis)


def build_mapping_candidates(analysis):
    from services.transcript_presentation import build_mapping_candidates as build
    return build(analysis)
