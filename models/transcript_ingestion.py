from dataclasses import dataclass, field
from typing import Literal

from models.course import Course
from models.transcript_extraction import ExtractionIssue, TranscriptExtraction


@dataclass
class IngestionDecision:
    """Application state, with no labels, messages or API response flags."""
    step: Literal["mapping_required", "weighting_required", "review_required", "complete"]
    extraction: TranscriptExtraction
    courses: list[Course] = field(default_factory=list)
    issues: list[ExtractionIssue] = field(default_factory=list)
    needs_review: bool = False
