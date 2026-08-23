# ---------------------------------------------------------------------------
# The canonical credential payload — the ONE data representation that gets
# signed (Phase 4) and later re-derived and checked against a signature
# (Phase 5). This module is the single source of truth for that
# representation; nothing else should build or serialize this shape.
#
# Determinism is the entire point: build_canonical_credential_payload()
# always produces the same dict for the same inputs, and
# canonicalize_credential_payload() always produces the same bytes for the
# same dict — sorted keys, compact separators, fixed UTF-8, no dict-repr
# ambiguity (str(dict) is explicitly NOT used, since Python's dict repr is
# an implementation detail, not a serialization format).
# ---------------------------------------------------------------------------

import json
from datetime import datetime, timezone
from decimal import Decimal


def _iso_utc(dt: datetime) -> str:
    """One deterministic ISO-8601 representation: UTC, second precision, 'Z' suffix. Requires a timezone-aware input."""
    if dt.tzinfo is None:
        raise ValueError("issued_at must be timezone-aware")
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def build_canonical_credential_payload(
    *,
    credential_identifier: str,
    student_identifier: str,
    student_name: str,
    institution_identifier: str,
    institution_name: str,
    credential_type: str,
    title: str,
    degree: str | None,
    graduation_year: int | None,
    cgpa: float | Decimal | None,
    document_hash: str,
    issued_at: datetime,
) -> dict:
    """
    Constructs the dict that gets signed. Every field is explicit — no
    **kwargs passthrough — so the shape of what's signed is visible in one
    place and can't silently drift when an unrelated caller adds a field.
    """
    return {
        "credential_identifier": credential_identifier,
        "student_identifier": student_identifier,
        "student_name": student_name,
        "institution_identifier": institution_identifier,
        "institution_name": institution_name,
        "credential_type": credential_type,
        "title": title,
        "degree": degree,
        "graduation_year": graduation_year,
        "cgpa": float(cgpa) if cgpa is not None else None,
        "document_hash": document_hash,
        "issued_at": _iso_utc(issued_at),
    }


def canonicalize_credential_payload(payload: dict) -> bytes:
    """
    Deterministic serialization of a payload dict to bytes — this exact byte
    sequence is what gets signed and, in Phase 5, re-derived and verified
    against. sort_keys + compact separators + fixed UTF-8 means the same
    logical payload always produces the same bytes, independent of dict
    insertion order or Python version.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
