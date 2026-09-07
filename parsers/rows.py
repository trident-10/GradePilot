"""Shared transcript row recognition, independent of PDF and GPA weighting."""

from dataclasses import dataclass
import re

from core.grade_scale import GRADE_POINTS
from parsers.text_normalization import fold, normalize_text, number
from parsers.headers import is_course_identifier, recognize_header, split_cells
from parsers.summary_labels import is_summary_line


GRADE_PATTERN = re.compile(r"(?:" + "|".join(GRADE_POINTS) + r")")
CODE_PATTERN = re.compile(
    r"^\*?(?:\d{1,3}[.)]?\s+)?([A-Za-zÇĞİÖŞÜçğıöşü]{2,12})"
    r"\s*[-.]?\s*(\d{2,4}[A-Za-z]?)(?=\s|$)"
)
NUMBER_PATTERN = re.compile(r"[+-]?\d+(?:[.,]\d+)?")
YEAR_PATTERN = re.compile(r"\b((?:19|20)\d{2})\s*[-/]\s*((?:19|20)\d{2})\b")
TERM_PATTERN = re.compile(r"\b(guz|bahar|yaz|fall|autumn|spring|summer)\b")
TERMS = {"guz": "Güz", "fall": "Güz", "autumn": "Güz",
         "bahar": "Bahar", "spring": "Bahar", "yaz": "Yaz", "summer": "Yaz"}
BOUNDARY_PATTERN = re.compile(
    r"\b(toplam|total|gano|agno|gpa|cgpa|ortalama|aciklama|explanation|"
    r"ogrenci|student|sayfa|page|transcript|transkript|university|universitesi)\b"
)
LEGEND_HEADING = re.compile(
    r"^(?:aciklamalar\s*\(?explanations\)?|explanations|"
    r"not\s+baremi|grade\s+scale|kisaltmalar|abbreviations)\b"
)


def semester_label(line: str, year: str | None = None) -> str | None:
    normalized = fold(line)
    term = TERM_PATTERN.search(normalized)
    years = YEAR_PATTERN.search(normalized)
    if years:
        year = f"{years[1]}-{years[2]}"
    if term and year:
        return f"{year} {TERMS[term[1]]}"
    numbered = re.fullmatch(r"\s*(\d{1,2})[. ]*\s*(?:yariyil|donem|semester)\s*", normalized)
    if numbered:
        return f"{numbered[1]}. Yarıyıl"
    return None


def semester_sort_key(label: str | None) -> tuple[int, int, int] | None:
    normalized = fold(label or "")
    years = YEAR_PATTERN.search(normalized)
    term = TERM_PATTERN.search(normalized)
    if years and term:
        return int(years[1]), int(years[2]), {"Güz": 0, "Bahar": 1, "Yaz": 2}[TERMS[term[1]]]
    return None


@dataclass
class TranscriptRow:
    parts: list[str]
    semester: str | None
    line_index: int
    field_positions: dict[str, int] | None
    header_confidence: str = "high"
    name_relative_position: int | None = None
    grade_hint: int | None = None

    @property
    def grade_index(self) -> int | None:
        if self.grade_hint is not None:
            return self.grade_hint if GRADE_PATTERN.fullmatch(self.parts[self.grade_hint]) else None
        # A grade-like abbreviation inside a course name is not a grade cell.
        for i in range(len(self.parts) - 1, 1, -1):
            if GRADE_PATTERN.fullmatch(self.parts[i]) and (
                number(self.parts[i - 1]) is not None
                or (i + 1 < len(self.parts) and number(self.parts[i + 1]) is not None)
            ):
                return i
        return None


def read_rows(text: str) -> list[TranscriptRow]:
    """Join wrapped rows without crossing another course, semester or summary."""
    rows: list[TranscriptRow] = []
    current: TranscriptRow | None = None
    semester = None
    year = None
    fields = None
    previous_header = ""
    confidence = "high"
    name_position = None
    schema = None
    contexts = []
    in_legend = False
    for line_index, raw in enumerate(normalize_text(text).splitlines()):
        line = raw.strip()
        if not line:
            continue
        if LEGEND_HEADING.match(fold(line)):
            in_legend = True
            current = schema = fields = name_position = None
            previous_header = ""
            continue
        if in_legend:
            # A legend may quote course IDs beside a grade-scale table.
            # Resume only on an explicit semester or course-table header.
            if not semester_label(line) and recognize_header(raw) is None:
                continue
            in_legend = False
        state = (semester, year, fields, previous_header, confidence, name_position, schema)
        if line == "[[TABLE_BEGIN]]":
            contexts.append(state)
            current = None
            continue
        if line in {"[[TABLE_NEXT]]", "[[TABLE_END]]"} and contexts:
            semester, year, fields, previous_header, confidence, name_position, schema = contexts[-1]
            if line == "[[TABLE_END]]":
                contexts.pop()
            current = None
            continue
        if (is_summary_line(line) and recognize_header(raw) is None
                and not any(GRADE_PATTERN.fullmatch(part) for part in line.split())):
            current = None
            continue
        bound = schema.bind_cells(line) if schema else None
        if bound is not None:
            code = CODE_PATTERN.fullmatch(bound[0])
            bound[0] = (code[1] + code[2]).upper() if code else bound[0].upper()
            current = TranscriptRow(bound, semester, line_index, fields, confidence, name_position,
                                    2 + schema.data_columns.index("grade"))
            rows.append(current)
            continue
        # T+U is one hours cell, even when the PDF puts spaces around '+'.
        line = re.sub(r"(?<=\d)\s*\+\s*(?=\d)", "+", line).replace("|", " ")
        code = CODE_PATTERN.match(line)
        structural_code = re.match(r"^([A-Za-z0-9][A-Za-z0-9._/-]{1,23})\s+(.+)$", line) if schema else None
        if (code is None and structural_code and is_course_identifier(structural_code[1])
                and any(c.isalpha() for c in structural_code[2])
                and len(structural_code[2].split()) >= 3):
            parts = [structural_code[1].upper(), *structural_code[2].split()]
            current = TranscriptRow(parts, semester, line_index, fields, confidence, name_position)
            rows.append(current)
            continue
        if code:
            parts = [(code[1] + code[2]).upper(), *line[code.end():].split()]
            parts = [p.rstrip("*") if GRADE_PATTERN.fullmatch(p.rstrip("*")) else p for p in parts]
            current = TranscriptRow(parts, semester, line_index, fields, confidence, name_position)
            rows.append(current)
            continue
        years = YEAR_PATTERN.search(fold(line))
        if years:
            year = f"{years[1]}-{years[2]}"
        label = semester_label(line, year)
        if label or years:
            semester = label  # An incomplete new heading must not inherit the old term.
            current = None
            continue
        if BOUNDARY_PATTERN.search(fold(line)):
            current = None
            continue
        detected = recognize_header(raw)
        headerish = bool(re.search(r"\b(credit|credits|kredi|akts|ects|grade|not|notu)\b", fold(line)))
        if headerish:
            combined = previous_header + " " + line
            schema = detected or recognize_header(combined)
            fields = schema.field_positions if schema else None
            confidence = "high" if detected else "medium"
            name_position = schema.name_position if schema else None
            previous_header = line
            current = None
            continue
        if current is not None and current.grade_index is None:
            current.parts.extend(line.split())
    return rows


def course_name(row: TranscriptRow, positions: dict[str, int | None] | None = None) -> str:
    grade_index = row.grade_index
    end = grade_index if grade_index is not None else len(row.parts)
    positions = positions if positions is not None else row.field_positions
    before_grade = [position for position in (positions or {}).values()
                    if position is not None and position < 0]
    if grade_index is not None and row.name_relative_position is not None:
        end = grade_index + row.name_relative_position
    elif grade_index is not None and before_grade:
        end = grade_index + min(before_grade)
    else:
        while end > 1 and number(row.parts[end - 1]) is not None:
            end -= 1
    # In the known type/language schema, hours precede the selected credits.
    for i in range(1, end - 1):
        if row.parts[i] in {"Z", "S"} and fold(row.parts[i + 1]).rstrip(".") in {"tr", "ing", "eng", "en", "tur"}:
            if all(number(part) is not None for part in row.parts[i + 2:end]):
                end = i
                break
    return " ".join(row.parts[1:end])
