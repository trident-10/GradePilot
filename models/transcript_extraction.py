"""Parser output: extracted facts and provenance, without workflow/UI state."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from models.extracted_course import ExtractedCourse
from models.transcript_document import TranscriptDocument

if TYPE_CHECKING:
    from parsers.generic_analyzer import GenericTranscriptAnalysis
    from parsers.rows import TranscriptRow


@dataclass
class TranscriptExtraction:
    rows: list["TranscriptRow"]
    courses: list[ExtractedCourse]
    analysis: "GenericTranscriptAnalysis"
    field_positions: dict[str, int] = field(default_factory=dict)
    format_name: str = "generic"
    confidence: float = 0.0
    document: TranscriptDocument = field(default_factory=TranscriptDocument)


@dataclass(frozen=True)
class ExtractionIssue:
    code: str
    severity: str = "error"
    row_index: int | None = None
    count: int = 1


@dataclass
class ExtractionReport:
    issues: list[ExtractionIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ExtractionIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]
