# ---------------------------------------------------------------------------
# PDF upload validation + private storage. PDF only, for now.
#
# Validation does NOT trust the filename or the browser-supplied Content-Type
# alone — both are attacker-controlled. The one check that actually proves
# "this is a PDF" is the magic-byte signature at the start of the file.
# ---------------------------------------------------------------------------

import hashlib
import uuid
from pathlib import Path

from fastapi import UploadFile

from ..config import settings

ALLOWED_EXTENSIONS = {".pdf"}
ALLOWED_CONTENT_TYPES = {"application/pdf"}
PDF_MAGIC = b"%PDF-"


class UnsupportedDocumentTypeError(Exception):
    pass


class DocumentTooLargeError(Exception):
    pass


class EmptyDocumentError(Exception):
    pass


async def read_and_validate_pdf(upload: UploadFile) -> bytes:
    """
    Reads the full upload into memory and validates it. Raises one of the
    typed errors above on any failure — the caller (route) maps these to
    HTTP 415/413/400. Order matters: cheap header checks first, then read
    the body, then the expensive/authoritative magic-byte check.
    """
    filename = upload.filename or ""
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise UnsupportedDocumentTypeError(f"Unsupported file extension: {extension or '(none)'}. Only .pdf is accepted.")

    if upload.content_type not in ALLOWED_CONTENT_TYPES:
        raise UnsupportedDocumentTypeError(f"Unsupported content type: {upload.content_type}. Only application/pdf is accepted.")

    data = await upload.read()

    if len(data) == 0:
        raise EmptyDocumentError("Uploaded document is empty")

    if len(data) > settings.max_document_size_bytes:
        raise DocumentTooLargeError(
            f"Document exceeds the maximum size of {settings.max_document_size_bytes} bytes"
        )

    # The authoritative check: filename and Content-Type are both supplied
    # by the client and prove nothing on their own — this does.
    if not data.startswith(PDF_MAGIC):
        raise UnsupportedDocumentTypeError("File content is not a valid PDF (missing %PDF- header)")

    return data


def compute_sha256(data: bytes) -> str:
    """Returns the 64-character lowercase hex SHA-256 digest of `data`."""
    return hashlib.sha256(data).hexdigest()


def credential_document_path(credential_id: uuid.UUID) -> Path:
    return Path(settings.storage_path) / "credentials" / f"{credential_id}.pdf"


def student_document_path(document_id: uuid.UUID) -> Path:
    return Path(settings.storage_path) / "student_documents" / f"{document_id}.pdf"


def save_document(credential_id: uuid.UUID, data: bytes) -> str:
    """
    Writes the validated bytes under STORAGE_PATH using a server-generated
    filename (the credential's own UUID) — never the client-supplied
    filename. Returns the path as a plain string for internal use only; this
    value must never be sent to a client (see routes/credentials.py, which
    streams the file instead of returning this path).
    """
    path = credential_document_path(credential_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return str(path)


def save_student_document(document_id: uuid.UUID, data: bytes) -> str:
    """Same contract as save_document, for a student-uploaded (not-yet-verified) document — kept in its own storage subdirectory."""
    path = student_document_path(document_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return str(path)


def delete_document_if_exists(storage_path: str) -> None:
    """Best-effort cleanup for the orphaned-file-on-failed-transaction case (see credential_service.issue_credential)."""
    path = Path(storage_path)
    if path.exists():
        path.unlink()
