from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from api.upload_temp import UploadTooLargeError, save_upload_to_temp
from input.pdf_input import MAX_PDF_SIZE_BYTES, PdfValidationError
from models.parse_result import ParseResult
from parsers.credit_options import CreditOption, MappingCandidate
from parsers.gpa_weighting import FIELD_ECTS, FIELD_LOCAL_CREDIT
from parsers.transcript_parser import TranscriptStructureError


@pytest.fixture
def client():
    return TestClient(create_app())


def _pdf_upload(content: bytes, filename: str = "transcript.pdf"):
    return {
        "file": (filename, io.BytesIO(content), "application/pdf"),
    }


def test_non_pdf_upload_is_rejected(client):
    response = client.post(
        "/api/transcripts/analyze",
        files=_pdf_upload(b"this is not a pdf"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Yüklenen dosya geçerli bir PDF değil."
    assert "tmp" not in response.json()["detail"].lower()
    assert ":\\" not in response.json()["detail"]


def test_empty_pdf_is_rejected(client):
    response = client.post(
        "/api/transcripts/analyze",
        files=_pdf_upload(b""),
    )

    assert response.status_code == 400
    assert "boş" in response.json()["detail"].lower()


def test_oversized_upload_is_rejected(client, monkeypatch):
    def fail_if_called(path, **kwargs):
        raise AssertionError("process_transcript must not run for oversized upload")

    monkeypatch.setattr(
        "api.transcripts.process_transcript",
        fail_if_called,
    )

    payload = b"%PDF-" + (b"0" * MAX_PDF_SIZE_BYTES)
    response = client.post(
        "/api/transcripts/analyze",
        files=_pdf_upload(payload),
    )

    assert response.status_code == 413
    assert "10 MB" in response.json()["detail"]
    assert "tmp" not in response.json()["detail"].lower()


def test_successful_upload_reaches_transcript_service(client, monkeypatch):
    seen = {}

    def fake_process(path, **kwargs):
        seen["path"] = path
        seen["exists_during_processing"] = Path(path).exists()
        return ParseResult(
            courses=[],
            format_name="cankaya",
            confidence=1.0,
            requires_user_confirmation=False,
            requires_credit_selection=True,
            warnings=[],
            credit_options=[
                CreditOption(
                    label="Kredi",
                    field_key=FIELD_LOCAL_CREDIT,
                    sample_values=[4.0],
                    score=1.0,
                ),
                CreditOption(
                    label="AKTS / ECTS",
                    field_key=FIELD_ECTS,
                    sample_values=[6.0],
                    score=1.0,
                ),
            ],
        )

    monkeypatch.setattr(
        "api.transcripts.process_transcript",
        fake_process,
    )

    response = client.post(
        "/api/transcripts/analyze",
        files=_pdf_upload(b"%PDF-1.4 fake-but-enough-for-upload-layer"),
    )

    assert response.status_code == 200
    assert seen["exists_during_processing"] is True
    body = response.json()
    assert body["status"] == "credit_selection"
    assert body["format"] == "cankaya"
    assert body["credit_options"] == [
        {"id": "credit", "label": "Kredi"},
        {"id": "ects", "label": "AKTS / ECTS"},
    ]
    assert "path" not in body
    serialized = str(body)
    assert "gradepilot_upload_" not in serialized
    assert ":\\" not in serialized


def test_initial_request_returns_credit_selection(client, monkeypatch):
    monkeypatch.setattr(
        "api.transcripts.process_transcript",
        lambda path, **kwargs: ParseResult(
            courses=[],
            format_name="generic",
            confidence=0.0,
            requires_user_confirmation=True,
            requires_credit_selection=True,
            warnings=["select weighting"],
            credit_options=[
                CreditOption(
                    label="Kredi",
                    field_key="rel:-2",
                    sample_values=[3.0],
                    score=2.0,
                    relative_position=-2,
                ),
            ],
        ),
    )

    response = client.post(
        "/api/transcripts/analyze",
        files=_pdf_upload(b"%PDF-1.4 data"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "credit_selection"
    assert body["credit_options"][0]["id"] == "credit"
    assert "rel:" not in str(body)


def test_ambiguous_columns_return_safe_manual_mapping(client, monkeypatch):
    monkeypatch.setattr(
        "api.transcripts.process_transcript",
        lambda path, **kwargs: ParseResult(
            courses=[],
            format_name="generic",
            confidence=0.0,
            requires_user_confirmation=True,
            requires_credit_selection=False,
            warnings=["manual mapping required"],
            requires_manual_mapping=True,
            mapping_candidates=[
                MappingCandidate(
                    label="Sütun A",
                    field_key="rel:-2",
                    sample_values=[3.0, 4.0, 3.0, 2.0],
                    confidence="low",
                    relative_position=-2,
                ),
                MappingCandidate(
                    label="Sütun B",
                    field_key="rel:-1",
                    sample_values=[6.0, 7.0, 5.0, 6.0],
                    confidence="low",
                    relative_position=-1,
                ),
            ],
        ),
    )

    response = client.post(
        "/api/transcripts/analyze",
        files=_pdf_upload(b"%PDF-1.4 data"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "manual_mapping"
    assert body["courses"] == []
    assert body["credit_options"] == []
    assert body["mapping_candidates"] == [
        {
            "id": "column_a",
            "label": "Sütun A",
            "sample_values": [3.0, 4.0, 3.0, 2.0],
            "confidence": "low",
        },
        {
            "id": "column_b",
            "label": "Sütun B",
            "sample_values": [6.0, 7.0, 5.0, 6.0],
            "confidence": "low",
        },
    ]
    serialized = str(body)
    assert "rel:" not in serialized
    assert "Kredi Alanı" not in serialized
    assert "student" not in serialized.lower()
    assert "filename" not in serialized.lower()


def test_manual_mapping_is_reused_for_normalization(client, monkeypatch):
    calls = []

    def fake_process(
        path,
        gpa_weighting_field=None,
        semantic_field_positions=None,
        **kwargs,
    ):
        calls.append((gpa_weighting_field, semantic_field_positions))
        if semantic_field_positions is None:
            return ParseResult(
                courses=[],
                format_name="generic",
                confidence=0.0,
                requires_user_confirmation=True,
                requires_credit_selection=False,
                warnings=[],
                requires_manual_mapping=True,
                mapping_candidates=[
                    MappingCandidate(
                        label="Sütun A",
                        field_key="rel:-2",
                        sample_values=[3.0, 4.0],
                        confidence="low",
                        relative_position=-2,
                    ),
                    MappingCandidate(
                        label="Sütun B",
                        field_key="rel:-1",
                        sample_values=[6.0, 7.0],
                        confidence="low",
                        relative_position=-1,
                    ),
                ],
            )

        if gpa_weighting_field is None:
            return ParseResult(
                courses=[],
                format_name="generic",
                confidence=0.0,
                requires_user_confirmation=True,
                requires_credit_selection=True,
                warnings=[],
                credit_options=[
                    CreditOption(
                        label="Kredi",
                        field_key=FIELD_LOCAL_CREDIT,
                        sample_values=[3.0, 4.0],
                        score=8.0,
                    ),
                    CreditOption(
                        label="AKTS / ECTS",
                        field_key=FIELD_ECTS,
                        sample_values=[6.0, 7.0],
                        score=8.0,
                    ),
                ],
            )

        from models.course import Course

        return ParseResult(
            courses=[
                Course(
                    code="CENG101",
                    name="Programming",
                    gpa_credit=3.0,
                    local_credit=3.0,
                    ects=6.0,
                    grade="BA",
                    source_order=0,
                )
            ],
            format_name="generic",
            confidence=0.0,
            requires_user_confirmation=True,
            requires_credit_selection=False,
            warnings=[],
        )

    monkeypatch.setattr("api.transcripts.process_transcript", fake_process)

    response = client.post(
        "/api/transcripts/analyze",
        files=_pdf_upload(b"%PDF-1.4 data"),
        data={
            "local_credit_field": "column_a",
            "ects_field": "column_b",
            "weighting_field": "credit",
        },
    )

    assert response.status_code == 200
    assert calls[-1] == (
        FIELD_LOCAL_CREDIT,
        {FIELD_LOCAL_CREDIT: -2, FIELD_ECTS: -1},
    )
    body = response.json()
    assert body["status"] == "confirmation"
    assert body["courses"][0]["gpa_credit"] == 3.0
    assert body["courses"][0]["local_credit"] == 3.0
    assert body["courses"][0]["ects"] == 6.0


def test_same_manual_column_is_rejected(client, monkeypatch):
    monkeypatch.setattr(
        "api.transcripts.process_transcript",
        lambda path, **kwargs: ParseResult(
            courses=[],
            format_name="generic",
            confidence=0.0,
            requires_user_confirmation=True,
            requires_credit_selection=False,
            warnings=[],
            requires_manual_mapping=True,
            mapping_candidates=[
                MappingCandidate(
                    label="Sütun A",
                    field_key="rel:-1",
                    sample_values=[3.0],
                    confidence="low",
                    relative_position=-1,
                )
            ],
        ),
    )

    response = client.post(
        "/api/transcripts/analyze",
        files=_pdf_upload(b"%PDF-1.4 data"),
        data={
            "local_credit_field": "column_a",
            "ects_field": "column_a",
        },
    )

    assert response.status_code == 400
    assert "same numeric column" in response.json()["detail"]


def test_unrecognized_course_structure_is_a_distinct_error(client, monkeypatch):
    def fail(path, **kwargs):
        raise TranscriptStructureError("Transcript/ders yapısı tanınamadı.")

    monkeypatch.setattr("api.transcripts.process_transcript", fail)

    response = client.post(
        "/api/transcripts/analyze",
        files=_pdf_upload(b"%PDF-1.4 data"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Transcript/ders yapısı tanınamadı."


def test_valid_weighting_field_is_passed(client, monkeypatch):
    calls = []

    def fake_process(path, credit_relative_position=None, gpa_weighting_field=None):
        calls.append(
            {
                "gpa_weighting_field": gpa_weighting_field,
            }
        )
        if gpa_weighting_field is None:
            return ParseResult(
                courses=[],
                format_name="cankaya",
                confidence=1.0,
                requires_user_confirmation=False,
                requires_credit_selection=True,
                warnings=[],
                credit_options=[
                    CreditOption(
                        label="Kredi",
                        field_key=FIELD_LOCAL_CREDIT,
                        sample_values=[4.0],
                        score=1.0,
                    ),
                    CreditOption(
                        label="AKTS / ECTS",
                        field_key=FIELD_ECTS,
                        sample_values=[6.0],
                        score=1.0,
                    ),
                ],
            )

        from models.course import Course

        return ParseResult(
            courses=[
                Course(
                    code="CENG111",
                    name="Programming",
                    gpa_credit=6.0,
                    grade="DD",
                    semester="2024-2025 Güz",
                    ects=6.0,
                    local_credit=4.0,
                )
            ],
            format_name="cankaya",
            confidence=1.0,
            requires_user_confirmation=False,
            requires_credit_selection=False,
            warnings=[],
            credit_options=None,
        )

    monkeypatch.setattr(
        "api.transcripts.process_transcript",
        fake_process,
    )

    response = client.post(
        "/api/transcripts/analyze",
        files=_pdf_upload(b"%PDF-1.4 data"),
        data={"weighting_field": "ects"},
    )

    assert response.status_code == 200
    assert calls[0]["gpa_weighting_field"] is None
    assert calls[1]["gpa_weighting_field"] == FIELD_ECTS
    body = response.json()
    assert body["status"] == "ready"
    assert body["courses"][0]["gpa_credit"] == 6.0
    assert body["courses"][0]["local_credit"] == 4.0
    assert body["courses"][0]["source_order"] == 0


def test_invalid_weighting_field_is_rejected(client, monkeypatch):
    monkeypatch.setattr(
        "api.transcripts.process_transcript",
        lambda path, **kwargs: ParseResult(
            courses=[],
            format_name="cankaya",
            confidence=1.0,
            requires_user_confirmation=False,
            requires_credit_selection=True,
            warnings=[],
            credit_options=[
                CreditOption(
                    label="Kredi",
                    field_key=FIELD_LOCAL_CREDIT,
                    sample_values=[4.0],
                    score=1.0,
                ),
            ],
        ),
    )

    response = client.post(
        "/api/transcripts/analyze",
        files=_pdf_upload(b"%PDF-1.4 data"),
        data={"weighting_field": "rel:-2"},
    )

    assert response.status_code == 400
    assert "Invalid weighting field" in response.json()["detail"]


def test_response_does_not_expose_temp_paths(client, monkeypatch):
    monkeypatch.setattr(
        "api.transcripts.process_transcript",
        lambda path, **kwargs: ParseResult(
            courses=[],
            format_name="cankaya",
            confidence=1.0,
            requires_user_confirmation=False,
            requires_credit_selection=True,
            warnings=[f"internal path was {path}"],
            credit_options=[
                CreditOption(
                    label="Kredi",
                    field_key=FIELD_LOCAL_CREDIT,
                    sample_values=[3.0],
                    score=1.0,
                ),
            ],
        ),
    )

    response = client.post(
        "/api/transcripts/analyze",
        files=_pdf_upload(b"%PDF-1.4 data"),
    )

    # Warnings come from backend; API should still avoid adding its own paths.
    # Our fake warning intentionally contains a path — ensure response schema
    # itself has no dedicated path field.
    assert response.status_code == 200
    assert "path" not in response.json()


def test_temp_upload_deleted_after_success(client, monkeypatch):
    seen = {}

    def fake_process(path, **kwargs):
        seen["path"] = path
        assert Path(path).exists()
        return ParseResult(
            courses=[],
            format_name="cankaya",
            confidence=1.0,
            requires_user_confirmation=False,
            requires_credit_selection=True,
            warnings=[],
            credit_options=[
                CreditOption(
                    label="Kredi",
                    field_key=FIELD_LOCAL_CREDIT,
                    sample_values=[3.0],
                    score=1.0,
                ),
            ],
        )

    monkeypatch.setattr(
        "api.transcripts.process_transcript",
        fake_process,
    )

    response = client.post(
        "/api/transcripts/analyze",
        files=_pdf_upload(b"%PDF-1.4 data"),
    )

    assert response.status_code == 200
    assert "path" in seen
    assert not Path(seen["path"]).exists()


def test_temp_upload_deleted_after_failure(client, monkeypatch):
    seen = {}

    def fake_process(path, **kwargs):
        seen["path"] = path
        assert Path(path).exists()
        raise PdfValidationError("PDF okunamadı. Farklı bir dosya deneyin.")

    monkeypatch.setattr(
        "api.transcripts.process_transcript",
        fake_process,
    )

    response = client.post(
        "/api/transcripts/analyze",
        files=_pdf_upload(b"%PDF-1.4 data"),
    )

    assert response.status_code == 400
    assert "path" in seen
    assert not Path(seen["path"]).exists()


def test_save_upload_to_temp_rejects_oversize_and_cleans_up(tmp_path, monkeypatch):
    stream = io.BytesIO(b"a" * (MAX_PDF_SIZE_BYTES + 1))
    created = {}

    real_named = __import__("tempfile").NamedTemporaryFile

    def tracking_named_temporary_file(*args, **kwargs):
        handle = real_named(*args, **kwargs)
        created["path"] = handle.name
        return handle

    monkeypatch.setattr(
        "api.upload_temp.tempfile.NamedTemporaryFile",
        tracking_named_temporary_file,
    )

    with pytest.raises(UploadTooLargeError):
        with save_upload_to_temp(stream):
            pass

    assert "path" in created
    assert not Path(created["path"]).exists()
