# ---------------------------------------------------------------------------
# Orchestrates anchoring one credential's hash on-chain. This module owns
# the *policy* (eligibility checks, idempotency, DB state transitions,
# activity logging); app/services/blockchain/client.py owns the actual
# web3 mechanics. Nothing here talks to web3 directly.
#
# CRITICAL invariant (see credential_payload.py / verification_service.py):
# the hash anchored here is sha256 of the EXACT SAME canonical payload bytes
# that Ed25519 already signs — reconstructed via
# verification_service.reconstruct_canonical_payload, the existing,
# unmodified function. This module does not build its own serialization of
# the credential.
# ---------------------------------------------------------------------------

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ...config import settings
from ...models.activity_log import ActivityLog
from ...models.credential import Credential
from ...models.enums import BlockchainAnchorStatus, CredentialStatus
from ...models.institution import Institution
from .. import verification_service
from .client import (
    BlockchainClient,
    BlockchainNotConfiguredError,
    BlockchainSubmissionError,
    CredentialAlreadyAnchoredOnChainError,
)


class CredentialNotFoundError(Exception):
    pass


class CredentialNotOwnedError(Exception):
    pass


class CredentialRevokedError(Exception):
    pass


class BlockchainNotConfiguredForAnchoringError(Exception):
    pass


class BlockchainAnchoringFailedError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def compute_blockchain_credential_hash(credential: Credential) -> str:
    """
    sha256 of the existing canonical credential payload, "0x"-prefixed hex
    (the on-chain bytes32 convention). Reuses
    verification_service.reconstruct_canonical_payload UNCHANGED — this is
    the same byte sequence Ed25519 already signs at issuance and re-checks
    at verification, so this hash is reproducible from the database alone,
    with no separate serialization to keep in sync.
    """
    canonical_bytes = verification_service.reconstruct_canonical_payload(credential)
    return "0x" + hashlib.sha256(canonical_bytes).hexdigest()


def anchor_credential(
    db: Session,
    institution: Institution,
    credential_id: uuid.UUID,
    *,
    client: BlockchainClient | None = None,
) -> Credential:
    """
    Idempotent: if already ANCHORED, returns the existing credential
    unchanged without submitting a new transaction. Otherwise computes the
    hash, marks PENDING (persisted before the network call so a crash
    mid-transaction leaves a visible PENDING marker rather than silence),
    submits it, and records ANCHORED or FAILED depending on the real
    outcome. A blockchain failure never touches status/signature/
    document_hash — the credential remains exactly as valid through the
    existing Ed25519 verification path as it was before this call.
    """
    credential = db.get(Credential, credential_id)
    if credential is None:
        raise CredentialNotFoundError()
    if credential.institution_id != institution.id:
        raise CredentialNotOwnedError()
    if credential.status == CredentialStatus.REVOKED:
        raise CredentialRevokedError()

    if credential.blockchain_status == BlockchainAnchorStatus.ANCHORED:
        return credential

    credential_hash = compute_blockchain_credential_hash(credential)

    credential.blockchain_credential_hash = credential_hash
    credential.blockchain_network = settings.blockchain_network_name
    credential.blockchain_status = BlockchainAnchorStatus.PENDING
    db.add(credential)
    db.commit()
    db.refresh(credential)

    try:
        active_client = client if client is not None else _build_default_client()
        result = active_client.anchor_hash(credential_hash)
    except CredentialAlreadyAnchoredOnChainError:
        # This exact hash is already on-chain (e.g. a prior attempt's
        # transaction actually succeeded even though we recorded FAILED
        # after a timed-out receipt wait). Recover by reading the existing
        # on-chain anchor rather than treating this as a new failure — the
        # hash genuinely is anchored, which is the fact this endpoint is
        # meant to guarantee.
        anchor_info = active_client.get_anchor(credential_hash)
        credential.blockchain_status = BlockchainAnchorStatus.ANCHORED
        credential.blockchain_anchored_at = datetime.fromtimestamp(anchor_info["timestamp"], tz=timezone.utc)
        credential.blockchain_contract_address = settings.blockchain_contract_address
        db.add(credential)
        db.commit()
        db.refresh(credential)
        return credential
    except BlockchainNotConfiguredError as exc:
        credential.blockchain_status = BlockchainAnchorStatus.FAILED
        db.add(credential)
        db.commit()
        db.refresh(credential)
        raise BlockchainNotConfiguredForAnchoringError() from exc
    except BlockchainSubmissionError as exc:
        credential.blockchain_status = BlockchainAnchorStatus.FAILED
        db.add(credential)
        db.commit()
        db.refresh(credential)
        raise BlockchainAnchoringFailedError(str(exc)) from exc

    credential.blockchain_status = BlockchainAnchorStatus.ANCHORED
    credential.blockchain_tx_hash = result["tx_hash"]
    credential.blockchain_contract_address = settings.blockchain_contract_address
    credential.blockchain_anchored_at = datetime.fromtimestamp(result["block_timestamp"], tz=timezone.utc)
    db.add(credential)

    db.add(
        ActivityLog(
            actor_user_id=institution.user_id,
            action="CREDENTIAL_ANCHORED",
            entity_type="credential",
            entity_id=credential.id,
            metadata_={
                "credential_identifier": credential.credential_identifier,
                "tx_hash": result["tx_hash"],
                "network": settings.blockchain_network_name,
            },
        )
    )

    db.commit()
    db.refresh(credential)
    return credential


def _build_default_client() -> BlockchainClient:
    return BlockchainClient()
