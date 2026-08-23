import uuid
from datetime import datetime

from pydantic import BaseModel

from ..models.enums import BlockchainAnchorStatus


class AnchorResponse(BaseModel):
    """
    Safe, public blockchain metadata for one credential. Never includes the
    backend signer's private key or any RPC credentials — those never leave
    app/services/blockchain/client.py.
    """

    credential_id: uuid.UUID
    status: BlockchainAnchorStatus
    transaction_hash: str | None
    network: str | None
    contract_address: str | None
    credential_hash: str | None
    anchored_at: datetime | None
