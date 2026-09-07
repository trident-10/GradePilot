"""Column schemas from explicit cells, with conservative plain-text fallback."""
from dataclasses import dataclass
import re
from parsers.text_normalization import fold


CELL_SEPARATOR = re.compile(r"\s*\|\s*|\t+| {2,}")
IDENTIFIER_ALIASES = {
    "code": ("code", "course code", "course id", "ders kodu", "ders kod", "kod", "kodu"),
    "name": ("course", "course name", "course title", "ders", "ders adi", "dersin adi", "adi"),
}


def is_course_identifier(value: str) -> bool:
    """Allow schema-backed numeric IDs and punctuated elective IDs (TE-II)."""
    return (re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{1,23}", value) is not None
            # Decimal amounts and numbered headings are not numeric course IDs.
            and re.fullmatch(r"\d+[.,]\d*", value) is None
            and re.fullmatch(r"(?:19|20)\d{2}[-/](?:19|20)\d{2}", value) is None
            and (any(c.isdigit() for c in value)
                 or re.search(r"[._/-][A-Za-z0-9]+$", value) is not None))


def split_cells(line: str) -> list[str]:
    return [cell.strip() for cell in CELL_SEPARATOR.split(line.strip().strip("|"))]


@dataclass(frozen=True)
class HeaderSchema:
    columns: tuple[str, ...]
    delimited: bool = False

    @property
    def data_columns(self) -> tuple[str, ...]:
        return tuple(column for column in self.columns if column not in {"code", "name"})

    @property
    def field_positions(self) -> dict[str, int]:
        columns = self.data_columns
        grade = columns.index("grade")
        return {field: columns.index(field) - grade for field in ("local_credit", "ects") if field in columns}

    @property
    def name_position(self) -> int:
        return -self.data_columns.index("grade")

    def bind_cells(self, line: str):
        """Preserve each explicit cell, including empty/unknown columns."""
        if not self.delimited or not {"code", "name"}.issubset(self.columns):
            return None
        cells = split_cells(line)
        if len(cells) != len(self.columns):
            return None
        code = cells[self.columns.index("code")]
        name = cells[self.columns.index("name")]
        if not (is_course_identifier(code) or re.fullmatch(r"[A-Za-z]{2,12}\s+\d{2,4}[A-Za-z]?", code)) or not any(c.isalpha() for c in name):
            return None
        data = [value or "?" for field, value in zip(self.columns, cells) if field not in {"code", "name"}]
        return [code, name, *data]


# Every recognized heading represents ONE data cell, including multiword labels.
# Unknown headings invalidate the plain-text fallback; explicit cells retain them.
HEADER_CELL = re.compile(
    r"\b(?P<local_credit>local\s+credit|course\s+credit|ulusal\s+kredi|"
    r"yerel\s+kredi|national\s+credits?|credits?|kredisi|kredi|uk)\b|"
    r"\b(?P<ects>akts\s*/\s*ects|ects\s*/\s*akts|akts|ects)\b|"
    r"\b(?P<other>t\s*\+\s*u(?:\s*\+\s*l)?|numeric\s+grade|sayisal\s+not|basari\s+notu|"
    r"grade\s+points?|quality\s+points?|not\s+katsayisi|katsayi|"
    r"puan|points?|score|teorik|uygulama|laboratuvar|hours?|t|u|l|"
    r"dersin\s+statusu|course\s+status|ogretim\s+dili|language|"
    r"aciklama|comment|durum|status|sonuc)\b|"
    r"\b(?P<grade>letter\s+grade|harf\s+notu|harf\s+not|harf|grade|notu|not)\b"
)


def recognize_header(line: str) -> HeaderSchema | None:
    cells = split_cells(line)
    if len(cells) >= 3:
        columns = []
        for cell in cells:
            normalized = fold(cell)
            field = next((key for key, aliases in IDENTIFIER_ALIASES.items() if normalized in aliases), None)
            match = HEADER_CELL.fullmatch(normalized)
            columns.append(field or (match.lastgroup if match else "unknown"))
        if (columns.count("grade") == 1
                and any(field in columns for field in ("local_credit", "ects"))
                and all(columns.count(field) <= 1 for field in ("local_credit", "ects", "code", "name"))):
            return HeaderSchema(tuple(columns), delimited=True)
    normalized = fold(line)
    matches = list(HEADER_CELL.finditer(normalized))
    columns = [match.lastgroup for match in matches]
    if columns.count("grade") != 1 or not any(field in columns for field in ("local_credit", "ects")):
        return None
    if any(columns.count(field) > 1 for field in ("local_credit", "ects")):
        return None
    if any(normalized[left.end():right.start()].strip(" \t|/:;()-.") for left, right in zip(matches, matches[1:])):
        return None
    if normalized[matches[-1].end():].strip(" \t|/:;()-."):
        # A neighbouring table's identifiers must not be swallowed as the
        # trailing portion of an otherwise valid flat header.
        return None
    return HeaderSchema(tuple(columns))


def header_positions(line: str) -> dict[str, int] | None:
    schema = recognize_header(line)
    return schema.field_positions if schema else None


