# ---------------------------------------------------------------------------
# Phase 9C: read-only blockchain anchor check, used by verification_service
# as one additional check alongside the existing Ed25519/document/status
# checks. This module NEVER submits a transaction — see client.get_anchor,
# which only calls the contract's `view` function.
#
# Design: the contract (CredentialAnchor.sol) stores anchors keyed BY hash
# (a mapping), so there is no on-chain way to ask "what hash was anchored
# for credential X" — only "does hash H exist as an anchor". Tamper
# detection therefore happens in two layers:
#
#   1. Locally: compare the hash recorded at anchor time
#      (credential.blockchain_credential_hash) against the hash recomputed
#      RIGHT NOW from the credential's current DB state. If these differ,
#      the credential's signed fields have changed since it was anchored —
#      that's MISMATCH, and it's detectable with zero network calls.
#   2. On-chain: only once the local check passes (nothing has changed) is
#      a live read-only call made, to independently confirm the anchor
#      still exists on the actual chain — this is the real "third party"
#      confirmation blockchain anchoring is for.
#
# This also means the extremely common case (a credential that was never
# anchored at all) never triggers a network call — status is decided
# entirely from credential.blockchain_status.
# ---------------------------------------------------------------------------

from ...models.credential import Credential
from ...models.enums import BlockchainAnchorStatus
from .client import BlockchainClient

# Deferred import (inside check_blockchain_anchor, not here) to avoid a
# circular import: anchoring_service imports verification_service (for
# reconstruct_canonical_payload), and verification_service imports this
# module. By call time (never at module-load time) both modules are fully
# initialized, so the deferred import resolves fine.

_NOT_ANCHORED_RESULT = {
    "status": "NOT_ANCHORED",
    "anchored": False,
    "hash_matches": None,
    "network": None,
    "contract_address": None,
    "transaction_hash": None,
    "anchored_at": None,
}


def _recorded_anchor_fields(credential: Credential) -> dict:
    return {
        "network": credential.blockchain_network,
        "contract_address": credential.blockchain_contract_address,
        "transaction_hash": credential.blockchain_tx_hash,
        "anchored_at": credential.blockchain_anchored_at,
    }


def check_blockchain_anchor(credential: Credential, *, client: BlockchainClient | None = None) -> dict:
    """
    Returns a dict matching the API's `blockchain` response shape:
    {status, anchored, hash_matches, network, contract_address,
    transaction_hash, anchored_at}. Never raises — any failure to reach the
    chain becomes an UNAVAILABLE result, never a silent "verified".

    PENDING and FAILED (an anchor attempt exists but never confirmed, or
    definitively failed) are both reported as NOT_ANCHORED here: from a
    verifier's point of view there is currently no confirmed anchor to
    trust either way, which is the honest summary of both states.
    """
    # No confirmed anchor on our own records — nothing to check on-chain,
    # and (per Phase 9A/9B) this is also exactly what a system with no
    # blockchain configured at all looks like: every credential simply has
    # blockchain_status=None. No network call needed either way.
    if credential.blockchain_status != BlockchainAnchorStatus.ANCHORED:
        return dict(_NOT_ANCHORED_RESULT)

    from .anchoring_service import compute_blockchain_credential_hash

    current_hash = compute_blockchain_credential_hash(credential)
    recorded = _recorded_anchor_fields(credential)

    if credential.blockchain_credential_hash != current_hash:
        # The credential's signed data has changed since it was anchored —
        # a tamper signal, independent of whether the chain is reachable.
        return {"status": "MISMATCH", "anchored": True, "hash_matches": False, **recorded}

    try:
        active_client = client if client is not None else BlockchainClient()
        onchain = active_client.get_anchor(current_hash)
    except Exception:
        # RPC unreachable, contract not configured, malformed response,
        # etc. — we believe (per our own DB) this credential was anchored,
        # but we could not independently confirm it right now.
        return {"status": "UNAVAILABLE", "anchored": True, "hash_matches": None, **recorded}

    if not onchain["exists"]:
        # Our records say anchored but the chain disagrees (e.g. pointed at
        # a different network, or a testnet reset) — surfaced as a mismatch
        # between records and on-chain reality rather than silently trusted.
        return {"status": "MISMATCH", "anchored": True, "hash_matches": False, **recorded}

    return {"status": "ANCHORED", "anchored": True, "hash_matches": True, **recorded}
