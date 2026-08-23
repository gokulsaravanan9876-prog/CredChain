# CredChain — Blockchain Credential Anchoring (Phase 9A/9B)

## Why blockchain, given Ed25519 already exists

CredChain already has a complete cryptographic trust chain: every credential
is SHA-256 hashed (its document, and the full canonical payload), signed
with the issuing institution's Ed25519 private key, and re-verified against
that signature on every verification request. That system is sufficient to
prove *"this credential was issued by this institution and has not been
altered,"* as long as a verifier trusts the institution's public key.

Blockchain anchoring adds one additional, independent property that
Ed25519 alone cannot: a **public, tamper-proof timestamp** that isn't
controlled by CredChain's own database. If CredChain's Postgres instance
were compromised and `issued_at` rewritten, the Ed25519 signature would
still check out (it doesn't cover a trusted clock) — but the on-chain
anchor transaction has its own independent block timestamp, on a network
neither CredChain nor the institution controls. Blockchain is a **second,
independent witness that this exact credential hash existed at this exact
time**, not a replacement for the signature that proves *who* issued it.

Ed25519 = authenticity ("this institution really signed this").
Blockchain anchor = independent timestamp ("this existed, unaltered, at
this block, before anyone could claim otherwise").

## What is stored on-chain

Per credential, exactly:

- `bytes32 credentialHash` — see "How the hash is generated" below
- `address issuer` — the backend service wallet that submitted the anchor transaction (`msg.sender`)
- `uint256 timestamp` — the anchoring block's timestamp
- `bool exists` — anchor presence flag

That's it. Nothing else is ever written to the contract.

## What is NOT stored on-chain

- The PDF document, or any part of it
- Student name, email, student ID
- Institution name
- CGPA, degree, graduation year, transcript content
- Any personally identifiable information whatsoever

`credentialHash` is a one-way SHA-256 digest. It reveals nothing about the
underlying credential data — it can only be used to *check* a specific
known credential against it, never to reconstruct or browse credential
content from the chain.

## How the hash is generated

**This is the single most important invariant of this phase.** The hash
anchored on-chain is derived from CredChain's existing, unmodified
canonical credential payload — the exact same byte sequence Ed25519 already
signs at issuance (`credential_payload.py`) and re-derives at verification
(`verification_service.reconstruct_canonical_payload`):

```
credential (DB row)
    → verification_service.reconstruct_canonical_payload(credential)
      [ = credential_payload.build_canonical_credential_payload(...)
          then credential_payload.canonicalize_credential_payload(...) ]
    → sha256(canonical_bytes)
    → "0x" + hex digest   =  blockchain_credential_hash
```

No new serialization format was introduced. `anchoring_service.py` imports
and calls the existing function directly — see
`test_blockchain_anchoring.py::test_hash_is_reproducible_and_uses_existing_canonical_payload`,
which proves the same DB row always reproduces the same hash and that the
hash is provably built from `canonicalize_credential_payload`'s real
output, not a parallel implementation.

This is *not* the same value as `document_hash` (the SHA-256 of the PDF
bytes alone) — `document_hash` is one input *into* the canonical payload;
`blockchain_credential_hash` is the hash of the whole payload (identifiers,
names, dates, and `document_hash` together). Anchoring the payload hash
means the anchor is sensitive to *any* signed field, not just the document.

## How anchoring works

1. Institution calls `POST /api/credentials/{credential_id}/anchor`.
2. `anchoring_service.anchor_credential` checks eligibility (institution
   owns the credential, credential is not revoked, not already anchored).
3. Computes `blockchain_credential_hash` as above; persists it with
   `blockchain_status = PENDING` *before* attempting the network call, so a
   crash mid-transaction leaves a visible marker rather than silence.
4. `blockchain/client.py`'s `BlockchainClient` (a thin `web3.py` wrapper)
   signs and submits `anchorCredential(credentialHash)` using the
   **backend service wallet** (see below), waits for the receipt.
5. On success: `blockchain_status = ANCHORED`, `blockchain_tx_hash`,
   `blockchain_anchored_at`, `blockchain_contract_address` are stored, and
   an `ActivityLog` row (`CREDENTIAL_ANCHORED`) is written.
6. On failure (RPC unreachable, out of gas, reverted, etc.):
   `blockchain_status = FAILED`. **The credential itself is never touched**
   — `status`, `signature`, `document_hash` are all untouched, and it
   remains fully verifiable through the existing Ed25519 path. Anchoring is
   additive; it can never invalidate a credential.
7. Anchoring the same credential again while already `ANCHORED` is a no-op:
   the existing anchor is returned, no second transaction is submitted.

Anchoring is **not** wired into credential issuance in this phase — issuing
a credential succeeds or fails purely on the existing Ed25519/PDF path,
completely independent of blockchain availability. Anchoring happens via
the explicit `POST .../anchor` endpoint, which is what section 9 of this
phase's spec calls for as the development/testing entry point. A
background job that automatically anchors every newly-issued credential
(with retry on `FAILED`) is reasonable future work, not built here — it
would need its own retry/backoff policy design, which is out of scope for
this phase's "do not overbuild" instruction.

## Network

**Polygon Amoy testnet** (chain id `80002`) — an EVM-compatible,
development-friendly public testnet. Never mainnet; `blockchain/scripts/deploy.py`
refuses to deploy to any chain id outside a small known-testnet allowlist
unless explicitly overridden.

## The signer: a backend service wallet, not a user's key

`BLOCKCHAIN_PRIVATE_KEY` is a wallet key that exists **only** to pay gas and
submit anchor transactions on the backend's behalf. It is completely
separate from every other key in this system:

| Key | Belongs to | Used for |
|---|---|---|
| Ed25519 signing key | the institution | signing the credential payload (unchanged, Phase 4) |
| `BLOCKCHAIN_PRIVATE_KEY` | the CredChain backend service | submitting anchor transactions |
| Student/company keys | — | none exist; students and companies never sign anything on-chain |

It is never returned in any API response, never logged, never present in
frontend source, and never committed to git (`.env` is git-ignored;
`.env.example` only has empty placeholders). For an actual production
deployment, this should be replaced with a KMS/HSM-backed signer or a
managed wallet service (e.g. AWS KMS, GCP KMS, or a custody provider) —
plaintext-env-var key storage is a dev-only convenience, documented here
rather than hidden.

## Smart contract

`contracts/CredentialAnchor.sol` — ~40 lines, two functions:

- `anchorCredential(bytes32 credentialHash)` — reverts with
  `AlreadyAnchored` if this hash was already anchored (write-once per hash,
  never a silent overwrite).
- `getCredentialAnchor(bytes32 credentialHash) view returns (address issuer, uint256 timestamp, bool exists)`

Emits `CredentialAnchored(credentialHash, issuer, timestamp)` on success.

## Deploying the contract

```bash
pip install web3 py-solc-x
export BLOCKCHAIN_RPC_URL=https://rpc-amoy.polygon.technology
export BLOCKCHAIN_CHAIN_ID=80002
export BLOCKCHAIN_PRIVATE_KEY=0x...   # a dev wallet, funded with testnet MATIC only
python blockchain/scripts/deploy.py
```

Get testnet funds from the Polygon Amoy faucet before deploying — the
script checks the deployer's balance and refuses to proceed at zero. On
success it prints the deployed address and writes
`contracts/CredentialAnchor.abi.json`, which `backend/app/services/blockchain/client.py`
reads at runtime. Copy the printed address into `backend/.env` as
`BLOCKCHAIN_CONTRACT_ADDRESS`.

## Backend environment variables

Set in `backend/.env` (see `backend/.env.example`):

```
BLOCKCHAIN_ENABLED=false            # true to actually attempt anchoring
BLOCKCHAIN_RPC_URL=                 # e.g. https://rpc-amoy.polygon.technology
BLOCKCHAIN_CHAIN_ID=80002
BLOCKCHAIN_NETWORK_NAME=polygon-amoy
BLOCKCHAIN_PRIVATE_KEY=             # backend service wallet — testnet funds only
BLOCKCHAIN_CONTRACT_ADDRESS=        # from deploy.py's output
```

With `BLOCKCHAIN_ENABLED=false` (the default), the anchor endpoint fails
cleanly with `blockchain_status = FAILED` and HTTP 503 instead of
attempting any network call — the same fallback pattern already used for
`AI_ENABLED`.

## Project structure

```
blockchain/
  contracts/
    CredentialAnchor.sol       — the contract source
    CredentialAnchor.abi.json  — compiled ABI (generated by deploy.py; read by the backend)
  scripts/
    deploy.py                  — compiles + deploys to the configured network
  README.md                    — this file
```
