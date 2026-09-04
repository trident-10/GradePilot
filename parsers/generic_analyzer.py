from dataclasses import dataclass
import re


@dataclass
class CreditCandidate:
    relative_position: int
    values: list[float]
    score: float
    label: str | None = None


@dataclass
class GenericTranscriptAnalysis:
    credit_candidates: list[CreditCandidate]


GRADE_PATTERN = re.compile(
    r"\b(AA|BA|BB|CB|CC|DC|DD|FD|FF)\b"
)


CREDIT_LABELS = {
    "uk": "Yerel Kredi / UK",
    "kredi": "Kredi",
    "credit": "Credit",
    "credits": "Credit",
    "akts": "AKTS / ECTS",
    "ects": "AKTS / ECTS",
}


def calculate_candidate_score(
    values: list[float]
) -> float:

    if not values:
        return 0.0

    score = 0.0

    positive_values = [
        value
        for value in values
        if value > 0
    ]

    positive_ratio = (
        len(positive_values)
        / len(values)
    )

    score += positive_ratio * 5.0

    reasonable_values = [
        value
        for value in values
        if 0 < value <= 15
    ]

    reasonable_ratio = (
        len(reasonable_values)
        / len(values)
    )

    score += reasonable_ratio * 3.0

    if all(
        value == 0
        for value in values
    ):
        score -= 10.0

    return score


def find_header_labels(
    text: str
) -> list[str]:

    detected_labels = []

    for line in text.splitlines():

        normalized_line = (
            line.lower()
            .replace("ı", "i")
            .replace("İ", "i")
        )

        for keyword, label in CREDIT_LABELS.items():

            if keyword in normalized_line:

                if label not in detected_labels:
                    detected_labels.append(
                        label
                    )

    return detected_labels


def assign_candidate_labels(
    candidates: list[CreditCandidate],
    detected_labels: list[str]
) -> None:

    if not detected_labels:
        return

    if len(detected_labels) != len(candidates):
        return

    ordered_candidates = sorted(
        candidates,
        key=lambda candidate:
        candidate.relative_position
    )

    for candidate, label in zip(
        ordered_candidates,
        detected_labels
    ):
        candidate.label = label


def analyze_generic_transcript(
    text: str
) -> GenericTranscriptAnalysis:

    candidate_columns: dict[
        int,
        list[float]
    ] = {}

    for line in text.splitlines():

        parts = line.split()

        if not parts:
            continue

        grade_index = None

        for index, part in enumerate(parts):

            if GRADE_PATTERN.fullmatch(part):
                grade_index = index
                break

        if grade_index is None:
            continue

        for index in range(grade_index):

            try:
                value = float(
                    parts[index]
                )
            except ValueError:
                continue

            relative_position = (
                index - grade_index
            )

            if (
                relative_position
                not in candidate_columns
            ):
                candidate_columns[
                    relative_position
                ] = []

            candidate_columns[
                relative_position
            ].append(value)

    candidates = []

    for relative_position, values in (
        candidate_columns.items()
    ):

        score = calculate_candidate_score(
            values
        )

        if score <= 2.0:
            continue

        candidates.append(
            CreditCandidate(
                relative_position=relative_position,
                values=values,
                score=score,
            )
        )

    detected_labels = find_header_labels(
        text
    )

    assign_candidate_labels(
        candidates=candidates,
        detected_labels=detected_labels
    )

    candidates.sort(
        key=lambda candidate:
        candidate.score,
        reverse=True
    )

    return GenericTranscriptAnalysis(
        credit_candidates=candidates
    )