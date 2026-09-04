from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from models.course import Course

if TYPE_CHECKING:
    from parsers.credit_options import CreditOption


@dataclass
class ParseResult:
    courses: list[Course]
    format_name: str
    confidence: float
    requires_user_confirmation: bool
    requires_credit_selection: bool
    warnings: list[str]
    credit_options: list[CreditOption] | None = None
