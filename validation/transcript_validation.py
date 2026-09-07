from models.transcript_extraction import ExtractionIssue, ExtractionReport, TranscriptExtraction
from parsers.rows import CODE_PATTERN, GRADE_PATTERN, number


NON_GPA_STATUSES = {"MU", "MUF", "M", "EX", "EXEMPT", "G", "P", "NP", "W", "I", "IP", "S", "U"}


def validate_transcript(extraction: TranscriptExtraction) -> ExtractionReport:
    """Return issues with source row indices; never choose a UI step or raise."""
    report = ExtractionReport()
    official_values = {}
    for observation in extraction.document.observations:
        official_values.setdefault((observation.semester, observation.field_name), set()).add(observation.value)
    conflicts = sum(len(values) > 1 for values in official_values.values())
    if conflicts:
        report.issues.append(ExtractionIssue("conflicting_official_values", "warning", count=conflicts))
    rows = extraction.rows
    if not rows:
        report.issues.append(ExtractionIssue("no_course_structure"))
        return report
    excluded = 0
    missing_semesters = 0
    for row in rows:
        if any(
            CODE_PATTERN.match(" ".join(row.parts[index:index + 2]))
            and any(GRADE_PATTERN.fullmatch(part) for part in row.parts[1:index])
            for index in range(2, len(row.parts))
        ):
            report.issues.append(ExtractionIssue("overlapping_tables", row_index=row.line_index))
        if row.grade_index is not None:
            for position in (row.field_positions or {}).values():
                index = row.grade_index + position
                value = number(row.parts[index]) if 1 <= index < len(row.parts) else None
                if value is None or value < 0:
                    report.issues.append(ExtractionIssue("invalid_credit_cells", row_index=row.line_index))
                    break
            missing_semesters += row.semester is None
        elif (row.parts[row.grade_hint].upper() in NON_GPA_STATUSES if row.grade_hint is not None else any(
            part.upper() in NON_GPA_STATUSES
            and number(row.parts[index - 1]) is not None
            for index, part in enumerate(row.parts[1:], start=1)
        )):
            excluded += 1
        else:
            report.issues.append(ExtractionIssue("unreadable_course", row_index=row.line_index))
    if excluded == len(rows):
        report.issues.append(ExtractionIssue("no_gpa_courses"))
    elif not extraction.analysis.credit_candidates and extraction.format_name != "cankaya":
        report.issues.append(ExtractionIssue("no_credit_columns"))
    if excluded:
        report.issues.append(ExtractionIssue("excluded_courses", "warning", count=excluded))
    if missing_semesters:
        report.issues.append(ExtractionIssue("missing_semesters", "warning", count=missing_semesters))
    return report


def validate_selected_field(extraction: TranscriptExtraction, field: str) -> ExtractionReport:
    report = ExtractionReport()
    if (len(extraction.courses) != extraction.analysis.course_row_count
            or any(getattr(course, field, None) is None for course in extraction.courses)):
        report.issues.append(ExtractionIssue("incomplete_selected_credit"))
    return report

