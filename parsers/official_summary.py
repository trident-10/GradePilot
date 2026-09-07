"""Read labelled official summary values, independently of GPA calculations."""
import re
from dataclasses import dataclass

from models.transcript_document import (
    Semester, SemesterSummary, SummaryObservation, TranscriptDocument,
)
from parsers.rows import YEAR_PATTERN, semester_label
from parsers.text_normalization import fold, normalize_text, number


from parsers.summary_labels import (
    COMPLETED_TOTAL, LABELS, OVERALL_HEADING, SEMESTER_HEADING, SEMESTER_WORD,
)


_NUMBER = r"[+-]?\d+(?:[.,]\d+)?"
_UNITS = {
    "credit": r"(?:kredi(?:si)?|credits?)",
    "ects": r"(?:akts|ects)",
    "total_course_count": r"(?:ders|adet|courses?)",
    "semester_count": r"(?:donem|yariyil|semesters?|terms?)",
}


@dataclass(frozen=True)
class _Label:
    kind: str
    text: str
    start: int
    end: int


def _labelled_value(text: str, kind: str) -> float | None:
    """Read one labelled amount, allowing its unit or an explicit GPA scale."""
    annotated = text.strip(" \t:;|=")
    if kind in {"gpa", "cgpa"}:
        match = re.fullmatch(rf"({_NUMBER})\s*\(dortluk\s+sistem\s+uzerinden\)", annotated)
        if match:
            value = number(match[1])
            return value if value is not None and 0 <= value <= 4 else None
    elif kind in {"ects", "credit"}:
        match = re.fullmatch(rf"({_NUMBER})(?:\s+{_UNITS[kind]})?\s*\(degerlendirilen:\s*({_NUMBER})\)", annotated)
        if match:
            total, evaluated = map(number, match.groups())
            return total if total is not None and evaluated is not None and 0 <= evaluated <= total else None
    elif kind == "total_course_count":
        match = re.fullmatch(rf"({_NUMBER})\s+(?:ders|adet)\s*\(\d+\s+tekrar(?:\s+dahil)?\)", annotated.split("\t")[0])
        if match:
            return number(match[1])
    value_text = text.strip(" \t:;|=()[]")
    if kind in {"gpa", "cgpa"}:
        scaled = re.fullmatch(rf"({_NUMBER})\s*/\s*({_NUMBER})(?:\s+-\s+[^\d]+|\s+\([^\d()]+\)?)?", value_text)
        if scaled:
            value, scale = map(number, scaled.groups())
            if value is not None and scale in {4, 5, 10, 100} and 0 <= value <= scale:
                return value
            return None
    unit = _UNITS.get(kind)
    pattern = rf"({_NUMBER})(?:\s+{unit})?" if unit else rf"({_NUMBER})"
    match = re.fullmatch(pattern, value_text.strip(" /"))
    if match is None and unit:
        # An explicit unit closes the amount when another visual table cell follows.
        # Do not take the first number from arbitrary trailing prose or numeric lists.
        match = re.match(rf"({_NUMBER})\s+{unit}(?=\t| {{2,}})", value_text)
    return number(match[1]) if match else None


def _values(text: str) -> list[float] | None:
    tokens = re.split(r"[\s|/:;=]+", text.strip(" \t:;|/=()[]"))
    if not tokens or not tokens[0]:
        return None
    values = [number(token) for token in tokens]
    return values if all(value is not None for value in values) else None


def extract_official_document(text: str, rows, courses) -> TranscriptDocument:
    document = TranscriptDocument()
    semesters: dict[str, Semester] = {}

    def ensure_semester(label: str):
        if label not in semesters:
            years = YEAR_PATTERN.search(label)
            semesters[label] = Semester(
                label=label, year=years[0] if years else None,
                term=label[years.end():].strip() if years else None,
                summary=SemesterSummary(), source_order=len(semesters),
            )
        return semesters[label]

    semester = year = None
    scope = None
    contexts = []
    pending = None
    graduation_statuses = set()
    row_lines = {row.line_index for row in rows}
    for index, raw in enumerate(normalize_text(text).splitlines()):
        line = fold(raw.strip())
        if not line:
            continue
        if line == "[[table_begin]]":
            contexts.append((semester, year, scope))
            pending = None
            continue
        if line in {"[[table_next]]", "[[table_end]]"} and contexts:
            semester, year, scope = contexts[-1]
            if line == "[[table_end]]":
                contexts.pop()
            pending = None
            continue
        if index in row_lines:
            pending = None
            continue
        graduation = re.fullmatch(r"mezuniyet\s+durumu\s*:\s*(?:[✓✔]\s*)?(.+)", line)
        if graduation:
            # Keep the printed wording and accents, independently of numeric summaries.
            graduation_statuses.add(raw.split(":", 1)[1].strip().lstrip("✓✔").strip())
            scope = "overall"
            pending = None
            continue
        matches = []
        for found in LABELS.finditer(line):
            match = _Label(found.lastgroup, found[0], found.start(), found.end())
            if (matches and matches[-1].kind == match.kind
                    and not line[matches[-1].end:match.start].strip(" \t()[]/")):
                # Keep the full alias span so it cannot leak into a preceding value.
                previous = matches[-1]
                matches[-1] = _Label(match.kind, line[previous.start:match.end], previous.start, match.end)
            else:
                matches.append(match)
        years = YEAR_PATTERN.search(line)
        if years:
            year = f"{years[1]}-{years[2]}"
        label = semester_label(line, year)
        if label and (not matches or years):
            semester = label
            ensure_semester(label)
            scope = None
            pending = None
            if not matches:
                continue
        elif years and not matches:
            semester = None
            pending = None
            continue
        if OVERALL_HEADING.match(line) or any(COMPLETED_TOTAL.match(match.text) for match in matches):
            scope = "overall"
            pending = None
        elif SEMESTER_HEADING.match(line):
            scope = "semester"
            pending = None
        elif semester and any(match.kind == "gpa" for match in matches) and any(
            match.kind == "cgpa" for match in matches
        ):
            # DNO/GNO/TUK/TAKTS describe this semester, including the
            # cumulative GPA printed at that point in the student's history.
            scope = "semester"
            pending = None
        if (scope != "semester" and any(match.kind == "cgpa" for match in matches)
                and not any(match.kind == "gpa" for match in matches)):
            scope = "overall"

        # A bare course-table heading is not an official summary heading.
        if matches and all(match.kind in {"credit", "ects"} for match in matches):
            if (not any(COMPLETED_TOTAL.match(match.text) for match in matches)
                    and re.search(r"\b(course|ders|grade|not|notu|code|kodu)\b", line[:matches[0].start])):
                pending = None
                continue

        def targets_for(labels):
            has_cgpa = any(match.kind == "cgpa" for match in labels)
            targets = []
            for match in labels:
                kind = match.kind
                local = (kind == "gpa" or SEMESTER_WORD.search(match.text)
                         or scope == "semester" or (scope != "overall" and semester and not has_cgpa))
                if kind == "cgpa" and scope != "semester":
                    local = False
                if kind in {"total_course_count", "semester_count"}:
                    local = False
                if local and not semester:
                    targets.append(None)
                    continue
                field = ({"credit": "local_credit", "ects": "ects"}.get(kind, kind) if local
                         else {"credit": "total_local_credit", "ects": "total_ects"}.get(kind, kind))
                if not local and field == "gpa":
                    targets.append(None)
                else:
                    targets.append((field, semester if local else None, match.text))
            return targets

        readings = []
        if matches:
            previous_pending = pending
            targets = targets_for(matches)
            for offset, match in enumerate(matches):
                end = matches[offset + 1].start if offset + 1 < len(matches) else len(line)
                value = _labelled_value(line[match.end:end], match.kind)
                if value is not None and targets[offset]:
                    readings.append((targets[offset], value))
            header_only = not readings and all(
                not line[match.end:matches[i + 1].start if i + 1 < len(matches) else len(line)].strip(" \t|/:;=()[]")
                for i, match in enumerate(matches)
            )
            cell_indices = [line[:match.start].count("\t") for match in matches]
            pending = (targets, cell_indices, line.count("\t") + 1) if header_only else None
            if (previous_pending and not pending and len(readings) == len(matches)
                    and all(match.kind == "ects" and SEMESTER_WORD.search(match.text) for match in matches)
                    and all(target and target[0] in {"gpa", "cgpa"} for target in previous_pending[0])):
                # A vertically centred semester total can sit between the
                # DNO/GNO labels and their two values in the adjacent cells.
                pending = previous_pending
        elif pending:
            pending, cell_indices, cell_count = pending
            cells = line.split("\t")
            if cell_count > 1 and len(cells) == cell_count and len(set(cell_indices)) == len(pending):
                # Preserve the labelled cell when adjacent metadata also has
                # numeric values (e.g. ISCED code beside credits completed).
                line = "\t".join(cells[i] for i in cell_indices)
            if len(pending) == 1 and pending[0]:
                field = pending[0][0]
                kind = {"local_credit": "credit", "total_local_credit": "credit", "total_ects": "ects"}.get(field, field)
                value = _labelled_value(line, kind)
                values = [value] if value is not None else None
            else:
                values = _values(line)
            if values is not None and len(values) == len(pending):
                readings = [(target, value) for target, value in zip(pending, values) if target]
            pending = None
        for (field, term, printed_label), value in readings:
            if term:
                ensure_semester(term)
            document.observations.append(SummaryObservation(field, value, index, printed_label, term))

    # A scalar is available only when its printed observations agree. Keep all
    # source observations so validation can report conflicts without guessing.
    grouped = {}
    for observation in document.observations:
        grouped.setdefault((observation.semester, observation.field_name), set()).add(observation.value)
    for (term, field), values in grouped.items():
        target = ensure_semester(term).summary if term else document.summary
        if len(values) == 1:
            value = next(iter(values))
            if field in {"total_course_count", "semester_count"}:
                value = int(value) if value.is_integer() else None
            setattr(target, field, value)
    for order, row in enumerate(rows):
        if row.semester:
            ensure_semester(row.semester).course_source_orders.append(order)
    for course in courses:
        if course.semester:
            ensure_semester(course.semester).courses.append(course)
    document.semesters = list(semesters.values())
    if len(graduation_statuses) == 1:
        document.summary.graduation_status = next(iter(graduation_statuses))
    return document
