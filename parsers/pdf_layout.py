"""Local reading-order blocks built from words. Never crop or bisect a page."""
from dataclasses import dataclass
import re
from statistics import median

from parsers.headers import HEADER_CELL, recognize_header, split_cells
from parsers.rows import BOUNDARY_PATTERN, CODE_PATTERN, GRADE_PATTERN, TERM_PATTERN, fold, number, semester_label
from parsers.summary_labels import LABELS, is_summary_line


@dataclass
class PageBlock:
    columns: list[list[list[dict]]]

    @property
    def bbox(self):
        words = [word for column in self.columns for line in column for word in line]
        return (min(w["x0"] for w in words), min(w["top"] for w in words),
                max(w["x1"] for w in words), max(w["bottom"] for w in words))


def _word_lines(page) -> list[list[dict]]:
    words = page.extract_words(x_tolerance=2, y_tolerance=3)
    lines: list[list[dict]] = []
    for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if not lines or abs(lines[-1][0]["top"] - word["top"]) > 3:
            lines.append([])
        lines[-1].append(word)
    for line in lines:
        line.sort(key=lambda w: w["x0"])
    return lines


def _render_lines(lines: list[list[dict]]) -> str:
    repaired: list[list[dict]] = []
    for original_line in _join_annotated_summary_cells(lines):
        line = list(original_line)
        previous = repaired[-1] if repaired else []
        previous_text = " ".join(w["text"] for w in previous)
        text = " ".join(w["text"] for w in line)
        code = CODE_PATTERN.match(previous_text)
        grades = [i for i, w in enumerate(previous) if GRADE_PATTERN.fullmatch(w["text"])]
        if code and len(grades) == 1 and not CODE_PATTERN.match(text) and not BOUNDARY_PATTERN.search(fold(text)):
            numeric_start = grades[0]
            while numeric_start > 0 and number(previous[numeric_start - 1]["text"]) is not None:
                numeric_start -= 1
            code_end = previous[0]["x1"]
            if previous[0]["text"].isalpha() and len(previous) > 1:
                code_end = previous[1]["x1"]
            if (numeric_start < grades[0]
                    and line[0]["x0"] > code_end + 2
                    and line[-1]["x1"] < previous[numeric_start]["x0"] - 2
                    and 0 < line[0]["top"] - previous[0]["top"] < 2 * (previous[0]["bottom"] - previous[0]["top"])
                    and all(number(w["text"]) is None for w in line)):
                # A wrapped name belongs before status/language cells too.
                # Find its insertion point from its horizontal extent, not
                # the first numeric value (which follows those metadata).
                gap = max(10, 1.5 * (previous[0]["bottom"] - previous[0]["top"]))
                insert_at = next((i for i in range(1, numeric_start + 1)
                                  if previous[i]["x0"] > line[-1]["x1"] + 2
                                  and previous[i]["x0"] - previous[i - 1]["x1"] >= gap), numeric_start)
                previous[insert_at:insert_at] = line
                continue
        repaired.append(line)
    rendered = []
    index = 0
    while index < len(repaired):
        band = _stacked_header(repaired, index)
        if band is not None:
            end, schema = band
            rendered.extend(_line_text(line) for line in repaired[index:end])
            # Serialize the spatial order after preserving the printed band.
            labels = {"other": "Status", "local_credit": "Credit", "ects": "ECTS",
                      "grade": "Grade", "code": "Code", "name": "Course name"}
            rendered.append("\t".join(labels.get(field, "Unknown") for field in schema.columns))
            index = end
        else:
            rendered.append(_line_text(repaired[index]))
            index += 1
    return "\n".join(rendered)


def _join_annotated_summary_cells(lines):
    """Join one wrapped amount beside a vertically centred summary label."""
    result = []
    index = 0
    while index < len(lines):
        if index + 2 < len(lines):
            above, middle, below = lines[index:index + 3]
            amount = re.fullmatch(r"\d+(?:[.,]\d+)?\s+(kredi|credits?|akts|ects)\s+\(degerlendirilen:", fold(_line_text(above)))
            closing = re.fullmatch(r"\d+(?:[.,]\d+)?\)", _line_text(below))
            height = median(w["bottom"] - w["top"] for w in above + middle + below)
            if (amount and closing
                    and 0 < middle[0]["top"] - above[0]["top"] <= height
                    and 0 < below[0]["top"] - middle[0]["top"] <= height
                    and abs(above[0]["x0"] - below[0]["x0"]) <= 3):
                left = min(w["x0"] for w in above + below)
                right = max(w["x1"] for w in above + below)
                label_words = [w for w in middle if w["x1"] < left]
                # All words of the amount must fit the same empty cell; a
                # neighbouring label or value must never be merged into it.
                label = LABELS.fullmatch(fold(_line_text(label_words)).rstrip(":")) if label_words else None
                kind = "credit" if amount[1] in {"kredi", "credit", "credits"} else "ects"
                if label and label.lastgroup == kind and all(w["x1"] < left or w["x0"] > right for w in middle):
                    value = dict(above[0], text=_line_text(above) + " " + _line_text(below), x1=right)
                    result.append(sorted([*middle, value], key=lambda w: w["x0"]))
                    index += 3
                    continue
        result.append(lines[index])
        index += 1
    return result


def _stacked_header(lines, index):
    """Recover staggered headings inside one local table, using word bounds."""
    if index + 1 >= len(lines):
        return None
    first, second = lines[index:index + 2]
    height = median(w["bottom"] - w["top"] for w in first + second)
    if not 0 < second[0]["top"] - first[0]["top"] <= 1.5 * height:
        return None
    # The offset baseline must consist exclusively of separate header cells.
    if not all(HEADER_CELL.fullmatch(fold(w["text"])) for w in second):
        return None
    if any(a["x0"] < b["x1"] and b["x0"] < a["x1"] for a in first for b in second):
        return None
    merged = sorted(first + second, key=lambda w: w["x0"])
    header_text = _line_text(merged)
    cells = split_cells(header_text)
    if len(cells) > 1 and semester_label(cells[0]):
        header_text = "\t".join(cells[1:])
    schema = recognize_header(header_text)
    if schema is None:
        return None
    end = index + 2
    if end < len(lines):
        translation = _line_text(lines[end])
        if (lines[end][0]["top"] - second[0]["top"] <= 1.5 * height
                and translation.startswith("(")
                and "(grade)" in fold(translation)
                and "(ects)" in fold(translation)):
            end += 1
    return end, schema


def _line_text(line: list[dict]) -> str:
    """Retain explicit cell gaps instead of flattening them into word spaces."""
    threshold = max(10, median(w["bottom"] - w["top"] for w in line) * 1.5)
    parts = [line[0]["text"]]
    for left, right in zip(line, line[1:]):
        parts.append("\t" if right["x0"] - left["x1"] >= threshold else " ")
        parts.append(right["text"])
    return "".join(parts)


def _table_evidence(words: list[dict]) -> bool:
    text = " ".join(word["text"] for word in words)
    if semester_label(text):
        return True
    # Header aliases provide evidence, not a required university row template.
    if recognize_header(_line_text(words)) is not None:
        return True
    return (sum(number(word["text"]) is not None for word in words) >= 1
            and any(GRADE_PATTERN.fullmatch(word["text"]) for word in words)
            and any(any(c.isalpha() for c in word["text"]) for word in words[:2]))


def _parallel_fragments(line: list[dict]) -> list[list[dict]]:
    # A gap alone is insufficient: both sides must independently look tabular.
    # Dense transcripts use small type and gutters narrower than 24 points.
    minimum_gap = max(4, 2 * median(w["bottom"] - w["top"] for w in line))
    gaps = sorted(range(1, len(line)), key=lambda i: line[i]["x0"] - line[i - 1]["x1"], reverse=True)
    for index in gaps:
        if line[index]["x0"] - line[index - 1]["x1"] < minimum_gap:
            break
        left, right = line[:index], line[index:]
        # Translations of one semester heading above a full-width table are
        # one context, not two parallel tables whose context should be restored.
        left_term, right_term = semester_label(_line_text(left)), semester_label(_line_text(right))
        left_word = TERM_PATTERN.search(fold(_line_text(left)))
        right_word = TERM_PATTERN.search(fold(_line_text(right)))
        if (left_term and left_term == right_term
                and left_word and right_word and left_word[0] != right_word[0]
                and not any(GRADE_PATTERN.fullmatch(w["text"]) for w in line)
                and not recognize_header(_line_text(left))
                and not recognize_header(_line_text(right))):
            continue
        if (bool(semester_label(_line_text(left))) != bool(semester_label(_line_text(right)))
                and (recognize_header(_line_text(left)) or recognize_header(_line_text(right)))):
            # A semester title and its column headings share a header band.
            # They do not constitute two independent tables.
            continue
        if _table_evidence(left) and _table_evidence(right):
            return _parallel_fragments(left) + _parallel_fragments(right)
    return [line]


def _aligned_fragments(line: list[dict], columns: list[list[list[dict]]]) -> list[list[dict]] | None:
    """Reuse only the bounds of locally established tables, including footers.

    Every word must fit one table. A crossing word or a full-width note ends
    this block instead of creating a page-wide cut through unrelated content.
    """
    bounds = [(min(w["x0"] for row in column for w in row) - 2,
               max(w["x1"] for row in column for w in row) + 2) for column in columns]
    parts = [[] for _ in columns]
    for word in line:
        fits = [i for i, (left, right) in enumerate(bounds)
                if left <= word["x0"] and word["x1"] <= right]
        if len(fits) != 1:
            return None
        parts[fits[0]].append(word)
    occupied = [part for part in parts if part]
    if len(occupied) > 1:
        if not all(_table_evidence(part) or is_summary_line(_line_text(part)) for part in occupied):
            return None
    else:
        text = _line_text(occupied[0])
        if BOUNDARY_PATTERN.search(fold(text)) and not is_summary_line(text):
            return None
    return parts


def extract_page_blocks(page) -> list[PageBlock]:
    """Each original word belongs to exactly one bounded reading-order block."""
    lines = _word_lines(page.dedupe_chars())
    blocks = []
    index = 0
    while index < len(lines):
        fragments = _parallel_fragments(lines[index])
        if len(fragments) == 1:
            # Consecutive ordinary lines stay together for wrapped-name repair.
            plain = [lines[index]]
            index += 1
            while index < len(lines) and len(_parallel_fragments(lines[index])) == 1:
                plain.append(lines[index])
                index += 1
            blocks.append(PageBlock([plain]))
            continue
        columns = [[fragment] for fragment in fragments]
        last_top = lines[index][0]["top"]
        index += 1
        while index < len(lines):
            line = lines[index]
            height = median(w["bottom"] - w["top"] for w in line)
            if line[0]["top"] - last_top > 3 * height:
                break
            parts = _parallel_fragments(line)
            if any(semester_label(_line_text(part)) for part in parts):
                # A new pair of semesters starts a fresh local block.
                break
            if len(parts) == len(columns) and all(
                abs(part[0]["x0"] - column[0][0]["x0"]) <= 8
                for part, column in zip(parts, columns)
            ):
                for part, column in zip(parts, columns):
                    column.append(part)
            else:
                aligned = _aligned_fragments(line, columns)
                if aligned is None:
                    break
                for part, column in zip(aligned, columns):
                    if part:
                        column.append(part)
            last_top = line[0]["top"]
            index += 1
        blocks.append(PageBlock(columns))
    return blocks


def extract_page_text(page) -> str:
    rendered = []
    for block in extract_page_blocks(page):
        if len(block.columns) == 1:
            rendered.append(_render_lines(block.columns[0]))
        else:
            # Scope table context while serializing for the legacy text API.
            # These separators never contain document text or crop coordinates.
            rendered.append("[[TABLE_BEGIN]]")
            for index, column in enumerate(block.columns):
                if index:
                    rendered.append("[[TABLE_NEXT]]")
                rendered.append(_render_lines(column))
            rendered.append("[[TABLE_END]]")
    return "\n".join(rendered)


