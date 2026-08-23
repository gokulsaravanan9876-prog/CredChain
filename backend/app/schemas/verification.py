import uuid
from datetime import datetime

from pydantic import BaseModel

from ..models.enums import CredentialType


class VerifyRequest(BaseModel):
    credential_id: uuid.UUID
    # DEMO/TEST ONLY. Overrides the CGPA used when reconstructing the
    # canonical payload to verify against the REAL stored signature — this
    # is how the tamper demonstration proves the signature is real without
    # ever mutating the stored credential. A real verification never sets
    # this; the frontend's demo panel is the only caller that does.
    demo_cgpa_override: float | None = None


class VerificationChecks(BaseModel):
    issuer: bool
    signature: bool
    integrity: bool
    status: bool
    access: bool


class VerifiedCredentialPreview(BaseModel):
    """Deliberately minimal — no ids, no student identifiers beyond what's already printed on the credential itself, no internal storage details."""

    credential_identifier: str
    credential_type: CredentialType
    title: str
    degree: str | None
    graduation_year: int | None
    cgpa: float | None
    institution_name: str


class BlockchainVerification(BaseModel):
    """
    Phase 9C. `status` is one of ANCHORED / NOT_ANCHORED / MISMATCH /
    UNAVAILABLE — see app/services/blockchain/anchor_verification.py for
    exactly what each means. Every field is either real data read from
    Postgres/the chain, or null — nothing here is ever fabricated.
    """

    status: str
    anchored: bool
    hash_matches: bool | None
    network: str | None
    contract_address: str | None
    transaction_hash: str | None
    anchored_at: datetime | None


class VerifyResponse(BaseModel):
    result: str
    checks: VerificationChecks
    credential: VerifiedCredentialPreview | None = None
    # None only for NOT_FOUND/UNAUTHORIZED, where there's no credential to
    # check an anchor for at all — every other result includes it.
    blockchain: BlockchainVerification | None = None
    # PS3 Phase F: the original company request's requested-credential
    # labels, when this credential was reached via a request-linked share —
    # None when accessed some other way (nothing to compare against) or for
    # NOT_FOUND/UNAUTHORIZED.
    requested_credentials: list[str] | None = None
