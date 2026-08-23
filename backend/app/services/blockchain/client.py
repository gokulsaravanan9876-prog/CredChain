# ---------------------------------------------------------------------------
# Thin web3.py wrapper around the deployed CredentialAnchor contract.
#
# The signer here is a BACKEND SERVICE identity — configured entirely via
# BLOCKCHAIN_* environment variables (see app/config.py and
# blockchain/README.md) — never the institution's Ed25519 key
# (signing_service.py) and never anything derived from a student or
# company. It never appears in any API response; nothing in this module
# returns the private key, and nothing logs it.
#
# This module is intentionally the ONLY place web3.py is imported — routes
# and anchoring_service.py talk to a BlockchainClient instance, never to
# web3 directly, so there is exactly one place that knows how a transaction
# gets signed and sent.
# ---------------------------------------------------------------------------

import json
from pathlib import Path

from web3 import Web3
from web3.exceptions import ContractLogicError

from ...config import settings

_ABI_PATH = Path(__file__).resolve().parents[4] / "blockchain" / "contracts" / "CredentialAnchor.abi.json"


class BlockchainNotConfiguredError(Exception):
    """Raised when BLOCKCHAIN_ENABLED is false or required settings are missing."""


class BlockchainSubmissionError(Exception):
    """Raised when a transaction could not be submitted or confirmed on-chain."""


class CredentialAlreadyAnchoredOnChainError(Exception):
    """Raised when the contract reports this exact hash was already anchored (by anyone)."""


def _load_abi() -> list:
    if not _ABI_PATH.exists():
        raise BlockchainNotConfiguredError(
            f"Contract ABI not found at {_ABI_PATH}. Run blockchain/scripts/deploy.py "
            "(or compile the contract) first."
        )
    return json.loads(_ABI_PATH.read_text())


class BlockchainClient:
    """
    Wraps the connection, account, and contract instance needed to anchor a
    credential hash. Constructed from Settings, not from raw args, so there
    is one obvious place (app/config.py) that owns where these values come
    from.
    """

    def __init__(self) -> None:
        if not settings.blockchain_enabled:
            raise BlockchainNotConfiguredError("BLOCKCHAIN_ENABLED is false")
        if not settings.blockchain_rpc_url or not settings.blockchain_private_key or not settings.blockchain_contract_address:
            raise BlockchainNotConfiguredError(
                "BLOCKCHAIN_RPC_URL, BLOCKCHAIN_PRIVATE_KEY, and BLOCKCHAIN_CONTRACT_ADDRESS must all be set"
            )

        self.w3 = Web3(Web3.HTTPProvider(settings.blockchain_rpc_url))
        self.account = self.w3.eth.account.from_key(settings.blockchain_private_key)
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(settings.blockchain_contract_address),
            abi=_load_abi(),
        )

    def anchor_hash(self, credential_hash_hex: str) -> dict:
        """
        Submits anchorCredential(credentialHash) and waits for the receipt.
        credential_hash_hex is a "0x"-prefixed 32-byte hex string (bytes32).
        Returns {"tx_hash": "0x...", "block_timestamp": int} on success.
        Raises CredentialAlreadyAnchoredOnChainError if the contract's
        AlreadyAnchored revert fires; BlockchainSubmissionError for any
        other failure (network error, out of gas, reverted for another
        reason, etc.) — callers must treat both as "did not succeed."
        """
        try:
            if not self.w3.is_connected():
                raise BlockchainSubmissionError(f"Not connected to RPC at {settings.blockchain_rpc_url}")

            credential_hash = bytes.fromhex(credential_hash_hex.removeprefix("0x"))
            nonce = self.w3.eth.get_transaction_count(self.account.address)

            tx = self.contract.functions.anchorCredential(credential_hash).build_transaction(
                {
                    "chainId": settings.blockchain_chain_id,
                    "from": self.account.address,
                    "nonce": nonce,
                }
            )
            signed = self.w3.eth.account.sign_transaction(tx, private_key=settings.blockchain_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status != 1:
                raise BlockchainSubmissionError(f"Transaction reverted: {tx_hash.hex()}")

            block = self.w3.eth.get_block(receipt.blockNumber)
            return {"tx_hash": tx_hash.hex(), "block_timestamp": block["timestamp"]}

        except ContractLogicError as exc:
            if "AlreadyAnchored" in str(exc):
                raise CredentialAlreadyAnchoredOnChainError(credential_hash_hex) from exc
            raise BlockchainSubmissionError(str(exc)) from exc
        except (CredentialAlreadyAnchoredOnChainError, BlockchainSubmissionError):
            raise
        except Exception as exc:
            # Any other failure (RPC timeout, DNS failure, insufficient
            # funds, malformed response, ...) — never let this bubble up as
            # an unhandled exception into the anchoring service; always a
            # BlockchainSubmissionError so the caller's failure handling is
            # uniform regardless of *why* the chain call didn't work.
            raise BlockchainSubmissionError(str(exc)) from exc

    def get_anchor(self, credential_hash_hex: str) -> dict:
        """Read-only lookup — does not submit a transaction."""
        credential_hash = bytes.fromhex(credential_hash_hex.removeprefix("0x"))
        issuer, timestamp, exists = self.contract.functions.getCredentialAnchor(credential_hash).call()
        return {"issuer": issuer, "timestamp": timestamp, "exists": exists}
