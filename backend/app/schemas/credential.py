import uuid
from datetime import datetime

from pydantic import BaseModel

from ..models.enums import BlockchainAnchorStatus, CredentialStatus, CredentialType


class CredentialResponse(BaseModel):
    id: uuid.UUID
    credential_identifier: str
    student_id: uuid.UUID
    student_name: str
    institution_id: uuid.UUID
    institution_name: str
    credential_type: CredentialType
    title: str
    degree: str | None
    graduation_year: int | None
    cgpa: float | None
    status: CredentialStatus
    issued_at: datetime
    revoked_at: datetime | None
    # Public by nature: a SHA-256 hash and an Ed25519 signature reveal
    # nothing about the private key or the ability to forge one — this is
    # exactly the material a verifier will need in Phase 5.
    document_hash: str | None
    signature: str | None
    has_document: bool

    # Phase 9D: public blockchain anchor metadata for credential detail
    # pages. Never includes the backend signer's private key or any RPC
    # credentials — those never leave app/services/blockchain/client.py.
    blockchain_status: BlockchainAnchorStatus | None = None
    blockchain_network: str | None = None
    blockchain_contract_address: str | None = None
    blockchain_tx_hash: str | None = None
    blockchain_anchored_at: datetime | None = None

    model_config = {"from_attributes": True}


class BulkIssuanceItemResponse(BaseModel):
    student_id: uuid.UUID
    student_name: str | None
    status: str  # "issued" | "failed" — never a batch-wide claim, see BulkIssuanceResponse
    credential_id: uuid.UUID | None = None
    error: str | None = None


class BulkIssuanceResponse(BaseModel):
    results: list[BulkIssuanceItemResponse]


class StudentSummaryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    student_identifier: str
    credential_count: int

    model_config = {"from_attributes": True}
