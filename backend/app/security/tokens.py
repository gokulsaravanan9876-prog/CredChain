# ---------------------------------------------------------------------------
# Share-link token generation and hashing.
#
# The raw token is a 256-bit value from secrets.token_urlsafe — cryptographically
# unpredictable, not derived from any database ID, timestamp, or counter.
# Only its SHA-256 hash is ever persisted (share_grants.share_token_hash);
# the raw value is returned to the caller exactly once, at creation time,
# and is never stored, logged, or included in activity metadata anywhere.
#
# Token lookup is by exact hash match via an indexed DB query — the standard
# pattern for bearer-token auth (this is what GitHub/Stripe-style API key
# verification does), not a manual byte-by-byte comparison of secrets in
# application code, which is the actual scenario constant-time comparison
# defends against.
# ---------------------------------------------------------------------------

import hashlib
import secrets

TOKEN_BYTES = 32  # 256 bits of entropy


def generate_raw_token() -> str:
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
