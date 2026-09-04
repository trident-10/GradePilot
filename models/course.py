from dataclasses import dataclass


@dataclass
class Course:
    code: str
    name: str
    gpa_credit: float
    grade: str
    semester: str | None = None
    ects: float | None = None
    # Preserved extracted local credit; engines use gpa_credit only.
    local_credit: float | None = None
    # Original transcript extraction order. Used to pick the latest
    # attempt of a repeated course. None means a legacy Course object
    # without parser metadata (see keep_latest_attempts fallback).
    source_order: int | None = None
