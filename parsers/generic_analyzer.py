from dataclasses import dataclass

from parsers.rows import number, read_rows
from parsers.semantic_fields import DetectionConfidence, SemanticField


@dataclass
class CreditCandidate:
    relative_position: int
    values: list[float]
    score: float
    confidence: DetectionConfidence = "low"
    semantic_field: SemanticField | None = None
    header_label: str | None = None


@dataclass
class GenericTranscriptAnalysis:
    credit_candidates: list[CreditCandidate]
    course_row_count: int


def calculate_candidate_score(values: list[float]) -> float:
    if not values:
        return 0.0
    return (5 * sum(v > 0 for v in values) + 3 * sum(0 < v <= 15 for v in values)) / len(values)


def analyze_generic_transcript(text: str, *, rows=None) -> GenericTranscriptAnalysis:
    rows = [row for row in (read_rows(text) if rows is None else rows) if row.grade_index is not None]
    columns: dict[int, list[float]] = {}
    labels: dict[int, set[str | None]] = {}
    for row in rows:
        grade = row.grade_index
        row_values = {}
        named_columns = row.column_schema.candidate_columns if row.column_schema else None
        # Only the contiguous numeric table cells adjacent to the grade are
        # candidates. Digits in course codes/names are never offered as credits.
        for direction in (-1, 1):
            index = grade + direction
            while 1 <= index < len(row.parts):
                value = number(row.parts[index])
                if value is None:
                    break
                if value >= 0:
                    row_values[index - grade] = value
                index += direction
        for position in (row.field_positions or {}).values():
            index = grade + position
            value = number(row.parts[index]) if 1 <= index < len(row.parts) else None
            if value is not None and value >= 0:
                row_values[position] = value
        if named_columns is not None:
            # Hours, coefficients and quality points are known non-credit
            # fields even when their values look exactly like course credits.
            row_values = {p: v for p, v in row_values.items() if p in named_columns}
            for position in named_columns:
                index = grade + position
                value = number(row.parts[index]) if 1 <= index < len(row.parts) else None
                if value is not None and value >= 0:
                    row_values[position] = value
        for position, value in row_values.items():
            columns.setdefault(position, []).append(value)
            labels.setdefault(position, set()).add(named_columns.get(position) if named_columns is not None else None)

    candidates = {
        position: CreditCandidate(position, values, calculate_candidate_score(values),
                                  header_label=next(iter(labels[position])) if len(labels[position]) == 1 else None)
        for position, values in columns.items()
    }
    if rows and rows[0].field_positions:
        for field, position in rows[0].field_positions.items():
            values = []
            for row in rows:
                relative = (row.field_positions or {}).get(field)
                if relative is None:
                    break
                index = row.grade_index + relative
                value = number(row.parts[index]) if 1 <= index < len(row.parts) else None
                if value is None or value < 0:
                    break
                values.append(value)
            # Never promote a partial or inconsistent header to a reliable field.
            if len(values) == len(rows) and position in candidates:
                candidates[position] = CreditCandidate(
                    relative_position=position, values=values,
                    score=calculate_candidate_score(values), semantic_field=field,
                    confidence="medium" if any(r.header_confidence == "medium" for r in rows) else "high",
                    header_label=candidates[position].header_label,
                )
    return GenericTranscriptAnalysis(
        credit_candidates=sorted(candidates.values(), key=lambda c: c.score, reverse=True),
        course_row_count=len(rows),
    )
