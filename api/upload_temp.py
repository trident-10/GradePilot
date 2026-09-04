from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator

from input.pdf_input import MAX_PDF_SIZE_BYTES, PDF_ERROR_TOO_LARGE


CHUNK_SIZE = 64 * 1024


class UploadTooLargeError(ValueError):
    """Raised when the HTTP upload exceeds the configured size limit."""


@contextmanager
def save_upload_to_temp(
    stream: BinaryIO,
    *,
    max_bytes: int = MAX_PDF_SIZE_BYTES,
    chunk_size: int = CHUNK_SIZE,
) -> Iterator[str]:
    """
    Stream an upload into a server-generated temporary PDF path.

    Does not use the client filename as a filesystem path.
    Guarantees temp file removal on success and failure.
    """

    temp_file = tempfile.NamedTemporaryFile(
        prefix="gradepilot_upload_",
        suffix=".pdf",
        delete=False,
    )
    temp_path = Path(temp_file.name)
    total = 0

    try:
        try:
            while True:
                chunk = stream.read(chunk_size)
                if not chunk:
                    break

                total += len(chunk)
                if total > max_bytes:
                    raise UploadTooLargeError(PDF_ERROR_TOO_LARGE)

                temp_file.write(chunk)

            temp_file.flush()
        finally:
            temp_file.close()

        yield str(temp_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()
