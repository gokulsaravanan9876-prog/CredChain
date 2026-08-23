# ---------------------------------------------------------------------------
# Institution signing-key lifecycle: generate once, store the public half in
# Postgres (institutions.public_key), keep the private half server-side only.
#
# DEV KEY MANAGEMENT (documented tradeoff, not hidden):
# Private keys are stored as plain PEM files on disk under KEYS_PATH, one
# per institution (<institution_id>.pem), git-ignored. This is NOT
# encrypted-at-rest and relies entirely on filesystem access control — fine
# for a hackathon MVP where "server-side only, never in the DB unencrypted"
# is the actual requirement, but a real deployment should upgrade this to a
# managed KMS/HSM (AWS KMS, GCP KMS, HashiCorp Vault, etc.) that never lets
# the private key material touch application disk at all. The seam for that
# upgrade is exactly this module — sign_credential_payload()'s callers don't
# know or care how/where the key is stored.
# ---------------------------------------------------------------------------

import base64
from pathlib import Path

from sqlalchemy.orm import Session

from ..config import settings
from ..models.institution import Institution
from ..security import signatures


class InstitutionKeyMissingError(Exception):
    pass


def _private_key_path(institution_id) -> Path:
    return Path(settings.keys_path) / f"{institution_id}.pem"


def ensure_institution_keypair(db: Session, institution: Institution) -> None:
    """
    Idempotent: if this institution already has a public key on record, does
    nothing — a stable signing identity is the whole point; regenerating on
    every call would silently invalidate every credential signed so far.
    Only generates + persists a new keypair when institution.public_key is
    still unset (i.e. this institution has never had one).
    """
    if institution.public_key is not None:
        return

    private_pem, public_pem = signatures.generate_keypair()

    key_path = _private_key_path(institution.id)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_bytes(private_pem)

    institution.public_key = public_pem.decode("utf-8")
    db.add(institution)
    db.commit()


def sign_credential_payload(institution: Institution, canonical_payload: bytes) -> str:
    """Signs already-canonicalized bytes with this institution's private key. Returns the signature, base64-encoded (safe for DB/API/JSON)."""
    key_path = _private_key_path(institution.id)
    if not key_path.exists():
        raise InstitutionKeyMissingError(f"No private signing key on this server for institution {institution.id}")

    private_pem = key_path.read_bytes()
    signature = signatures.sign(private_pem, canonical_payload)
    return base64.b64encode(signature).decode("ascii")
