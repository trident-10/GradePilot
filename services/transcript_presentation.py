"""User-facing labels and messages for transcript ingestion."""
from models.credit_fields import CreditOption, MappingCandidate, relative_field_key
from models.extracted_course import ExtractedCourse
from parsers.generic_analyzer import GenericTranscriptAnalysis
from parsers.semantic_fields import FIELD_ECTS, FIELD_LOCAL_CREDIT, RELIABLE_CONFIDENCES
from models.transcript_extraction import ExtractionIssue
from models.transcript_ingestion import IngestionDecision
from models.parse_result import ParseResult


ISSUE_MESSAGES = {
    "no_course_structure": "Transcript/ders yapısı tanınamadı.",
    "overlapping_tables": "Yan yana ders tabloları güvenle ayrılamadı.",
    "invalid_credit_cells": "Bazı derslerin Kredi/AKTS sütunları eksik veya kaymış görünüyor. Eksik derslerle GANO hesaplanamaz.",
    "unreadable_course": "Bazı ders satırlarının notu veya sütun yapısı okunamadı. Eksik derslerle GANO hesaplanamaz.",
    "no_gpa_courses": "GANO hesabına uygun harf notlu ders bulunamadı.",
    "no_credit_columns": "Dersler bulundu ancak kredi sütunları okunamadı.",
    "excluded_courses": "{count} dersin muafiyet, devam veya geçer/kalır durumu GANO hesabına dahil edilmedi.",
    "missing_semesters": "Bazı derslerin dönem bilgisi bulunamadı; dönem dağılımını kontrol edin.",
    "incomplete_selected_credit": "Bazı derslerin seçilen kredi alanı okunamadı. Eksik derslerle GANO hesaplanamaz.",
    "conflicting_official_values": "Transkriptte aynı resmi özet alanı için farklı değerler bulundu; kaynak değerleri kontrol edin.",
}


def issue_message(issue: ExtractionIssue) -> str:
    return ISSUE_MESSAGES[issue.code].format(count=issue.count)


def present_transcript(decision: IngestionDecision) -> ParseResult:
    extraction = decision.extraction
    warnings = [issue_message(issue) for issue in decision.issues if issue.severity == "warning"]
    messages = {"mapping_required": "mapping", "weighting_required": "weighting", "review_required": "confirmation"}
    if decision.step in messages:
        warnings.insert(0, WORKFLOW_MESSAGES[messages[decision.step]])
    options = None
    if decision.step == "weighting_required":
        if extraction.format_name == "cankaya":
            options = build_weighting_options_from_extracted(extraction.courses)
        else:
            by_position = {c.relative_position: c for c in extraction.analysis.credit_candidates}
            options = [CreditOption(
                label="Kredi" if semantic == "local_credit" else "AKTS / ECTS",
                field_key=semantic, relative_position=position,
                sample_values=by_position[position].values[:5],
                score=by_position[position].score, confidence=by_position[position].confidence,
            ) for semantic, position in sorted(extraction.field_positions.items(), key=lambda item: item[0] != "local_credit")]
    return ParseResult(
        courses=decision.courses, format_name=extraction.format_name,
        confidence=extraction.confidence, requires_user_confirmation=decision.needs_review,
        requires_credit_selection=decision.step == "weighting_required",
        requires_manual_mapping=decision.step == "mapping_required",
        credit_options=options,
        mapping_candidates=build_mapping_candidates(extraction.analysis) if decision.step == "mapping_required" else None,
        warnings=warnings,
        document=extraction.document,
    )


WORKFLOW_MESSAGES = {
    "mapping": "Dersler bulundu ancak Kredi/AKTS sütunları güvenle belirlenemedi.",
    "weighting": "GANO hesabında hangi kredi alanının kullanılacağını seçmelisiniz.",
    "confirmation": "Ders bilgilerini, kredileri ve dönem dağılımını kontrol edip onaylayın.",
}

def build_credit_options(
    analysis: GenericTranscriptAnalysis
) -> list[CreditOption]:

    options: list[CreditOption] = []
    seen_fields: set[str] = set()

    for candidate in sorted(
        analysis.credit_candidates,
        key=lambda item: item.relative_position,
    ):
        semantic_field = candidate.semantic_field
        if (
            semantic_field is None
            or candidate.confidence not in RELIABLE_CONFIDENCES
            or semantic_field in seen_fields
        ):
            continue

        seen_fields.add(semantic_field)
        options.append(
            CreditOption(
                label=(
                    "Kredi"
                    if semantic_field == FIELD_LOCAL_CREDIT
                    else "AKTS / ECTS"
                ),
                field_key=semantic_field,
                sample_values=candidate.values[:5],
                score=candidate.score,
                confidence=candidate.confidence,
                relative_position=candidate.relative_position,
            )
        )

    return options


def build_mapping_candidates(
    analysis: GenericTranscriptAnalysis,
) -> list[MappingCandidate]:
    """Build frontend-safe labels while keeping parser positions internal."""

    candidates: list[MappingCandidate] = []

    for index, candidate in enumerate(
        sorted(
            analysis.credit_candidates,
            key=lambda item: item.relative_position,
        )
    ):
        letter = chr(ord("A") + index) if index < 26 else str(index + 1)
        candidates.append(
            MappingCandidate(
                label=f"Sütun {letter}",
                field_key=relative_field_key(candidate.relative_position),
                sample_values=candidate.values[:5],
                confidence=candidate.confidence,
                relative_position=candidate.relative_position,
            )
        )

    return candidates


def build_weighting_options_from_extracted(
    extracted_courses: list[ExtractedCourse],
) -> list[CreditOption]:
    """Offer only credit fields that were actually extracted."""

    options: list[CreditOption] = []

    local_values = [
        course.local_credit
        for course in extracted_courses
        if course.local_credit is not None
    ]
    ects_values = [
        course.ects
        for course in extracted_courses
        if course.ects is not None
    ]

    if local_values:
        options.append(
            CreditOption(
                label="Kredi",
                field_key=FIELD_LOCAL_CREDIT,
                sample_values=local_values[:5],
                score=1.0,
                confidence="high",
                relative_position=None,
            )
        )

    if ects_values:
        options.append(
            CreditOption(
                label="AKTS / ECTS",
                field_key=FIELD_ECTS,
                sample_values=ects_values[:5],
                score=1.0,
                confidence="high",
                relative_position=None,
            )
        )

    return options


