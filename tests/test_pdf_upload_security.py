from __future__ import annotations

import io
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fpdf import FPDF

from api.main import create_app
from api.upload_temp import UploadTooLargeError, save_upload_to_temp
from input.pdf_input import (
    MAX_PDF_PAGES,
    MAX_PDF_SIZE_BYTES,
    PDF_ERROR_NOT_PDF,
    PDF_ERROR_TOO_LARGE,
    PDF_ERROR_TOO_MANY_PAGES,
    PDF_ERROR_UNREADABLE,
    PdfValidationError,
    create_safe_temp_pdf,
    validate_pdf_file,
)
from models.parse_result import ParseResult
from parsers.credit_options import CreditOption
from parsers.gpa_weighting import FIELD_LOCAL_CREDIT


@pytest.fixture
def client():
    return TestClient(create_app())


def _pdf_bytes(*, pages: int = 1, encrypt: bool = False) -> bytes:
    pdf = FPDF()
    for index in range(pages):
        pdf.add_page()
        pdf.set_font("helvetica", size=11)
        pdf.cell(0, 10, f"Page {index + 1}")
    if encrypt:
        pdf.set_encryption(
            owner_password="owner-secret",
            user_password="user-secret",
        )
    return bytes(pdf.output())


def _credit_selection_result() -> ParseResult:
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
            )
        ],
    )


def _upload(
    content: bytes,
    filename: str = "transcript.pdf",
    content_type: str = "application/pdf",
):
    return {
        "file": (filename, io.BytesIO(content), content_type),
    }


class _HeaderlessStream:
    """Readable stream with no Content-Length / __len__ / seek."""

    def __init__(self, payload: bytes, chunk_size: int = 1024) -> None:
        self._payload = payload
        self._offset = 0
        self._chunk_size = chunk_size
        self.bytes_read = 0

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        take = self._chunk_size if size in (-1, None) else min(size, self._chunk_size)
        chunk = self._payload[self._offset : self._offset + take]
        self._offset += len(chunk)
        self.bytes_read += len(chunk)
        return chunk


def test_frontend_upload_limits_match_backend():
    source = Path(__file__).resolve().parents[1] / "web" / "lib" / "uploadLimits.ts"
    text = source.read_text(encoding="utf-8")
    assert "10 * 1024 * 1024" in text
    assert "MAX_TRANSCRIPT_PDF_PAGES = 50" in text
    assert MAX_PDF_SIZE_BYTES == 10 * 1024 * 1024
    assert MAX_PDF_PAGES == 50


def test_small_valid_pdf_is_accepted(client, monkeypatch):
    monkeypatch.setattr(
        "services.transcript_service.extract_text_from_pdf",
        lambda path: "unused",
    )
    monkeypatch.setattr(
        "services.transcript_service.analyze_and_parse_transcript",
        lambda **kwargs: _credit_selection_result(),
    )

    response = client.post(
        "/api/transcripts/analyze",
        files=_upload(_pdf_bytes(pages=1)),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "credit_selection"


def test_fake_extension_is_rejected_by_magic_bytes(client):
    response = client.post(
        "/api/transcripts/analyze",
        files=_upload(b"not a pdf at all", filename="transcript.pdf"),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == PDF_ERROR_NOT_PDF


def test_wrong_magic_bytes_are_rejected(tmp_path):
    path = tmp_path / "photo.pdf"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"not-a-pdf")
    with pytest.raises(PdfValidationError, match=PDF_ERROR_NOT_PDF):
        validate_pdf_file(str(path))


def test_too_many_pages_are_rejected_before_parse(client, monkeypatch):
    parsed = {"called": False}

    def fail_if_extract(path):
        parsed["called"] = True
        raise AssertionError("text extraction must not run for oversized page count")

    monkeypatch.setattr(
        "services.transcript_service.extract_text_from_pdf",
        fail_if_extract,
    )

    response = client.post(
        "/api/transcripts/analyze",
        files=_upload(_pdf_bytes(pages=MAX_PDF_PAGES + 1)),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == PDF_ERROR_TOO_MANY_PAGES
    assert parsed["called"] is False


def test_truncated_pdf_returns_controlled_error(client):
    response = client.post(
        "/api/transcripts/analyze",
        files=_upload(b"%PDF-1.4\n% truncated, no xref"),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == PDF_ERROR_UNREADABLE
    assert "Traceback" not in response.json()["detail"]
    assert "tmp" not in response.json()["detail"].lower()


def test_encrypted_pdf_returns_controlled_error(client):
    response = client.post(
        "/api/transcripts/analyze",
        files=_upload(_pdf_bytes(pages=1, encrypt=True)),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == PDF_ERROR_UNREADABLE


def test_save_upload_rejects_oversize_without_content_length():
    limit = 8 * 1024
    stream = _HeaderlessStream(b"a" * (limit + 1), chunk_size=512)
    with pytest.raises(UploadTooLargeError) as exc_info:
        with save_upload_to_temp(stream, max_bytes=limit, chunk_size=512):
            raise AssertionError("oversize stream must not be yielded")
    assert exc_info.value.args[0] == PDF_ERROR_TOO_LARGE
    assert stream.bytes_read <= limit + 512


def test_save_upload_success_and_exception_cleanup(monkeypatch):
    created: dict[str, str] = {}
    real_named = tempfile.NamedTemporaryFile

    def tracking_named_temporary_file(*args, **kwargs):
        handle = real_named(*args, **kwargs)
        created["path"] = handle.name
        return handle

    monkeypatch.setattr(
        "api.upload_temp.tempfile.NamedTemporaryFile",
        tracking_named_temporary_file,
    )

    with save_upload_to_temp(io.BytesIO(b"%PDF-1.4 ok")) as path:
        assert Path(path).exists()
        assert Path(path).name.startswith("gradepilot_upload_")
        assert created["path"] == path

    assert not Path(created["path"]).exists()

    with pytest.raises(UploadTooLargeError):
        with save_upload_to_temp(io.BytesIO(b"x" * 64), max_bytes=8):
            pass
    assert not Path(created["path"]).exists()


def test_create_safe_temp_pdf_cleans_up_when_copy_fails(tmp_path, monkeypatch):
    source = tmp_path / "ok.pdf"
    source.write_bytes(_pdf_bytes(pages=1))
    created: dict[str, str] = {}
    real_named = tempfile.NamedTemporaryFile

    class ExplodingFile:
        def __init__(self, *args, **kwargs):
            handle = real_named(*args, **kwargs)
            self.name = handle.name
            handle.close()
            created["path"] = self.name

        def write(self, data):
            raise OSError("disk full")

        def flush(self):
            return None

        def close(self):
            return None

    monkeypatch.setattr(
        "input.pdf_input.tempfile.NamedTemporaryFile",
        lambda *args, **kwargs: ExplodingFile(*args, **kwargs),
    )

    with pytest.raises(OSError, match="disk full"):
        create_safe_temp_pdf(str(source))
    assert "path" in created
    assert not Path(created["path"]).exists()


def test_client_filename_cannot_traverse_filesystem(client, monkeypatch):
    seen: dict[str, str] = {}

    monkeypatch.setattr(
        "services.transcript_service.extract_text_from_pdf",
        lambda path: seen.update(path=path) or "unused",
    )
    monkeypatch.setattr(
        "services.transcript_service.analyze_and_parse_transcript",
        lambda **kwargs: _credit_selection_result(),
    )

    nasty = "..\\..\\..\\Windows\\System32\\transcript.pdf"
    response = client.post(
        "/api/transcripts/analyze",
        files=_upload(_pdf_bytes(pages=1), filename=nasty),
    )
    assert response.status_code == 200
    temp_path = Path(seen["path"])
    assert "System32" not in seen["path"]
    assert ".." not in temp_path.name
    assert temp_path.name.startswith("gradepilot_")
    assert tempfile.gettempdir().lower() in str(temp_path).lower()
