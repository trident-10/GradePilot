from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from models.course import Course
from models.transcript_document import TranscriptDocument

if TYPE_CHECKING:
    from parsers.credit_options import CreditOption, MappingCandidate


@dataclass
class ParseResult:
    courses: list[Course]
    format_name: str
    confidence: float
    requires_user_confirmation: bool
    requires_credit_selection: bool
    warnings: list[str]
    credit_options: list[CreditOption] | None = None
    requires_manual_mapping: bool = False
    mapping_candidates: list[MappingCandidate] | None = None
    document: TranscriptDocument | None = None
