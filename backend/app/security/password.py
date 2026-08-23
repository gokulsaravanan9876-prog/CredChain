# ---------------------------------------------------------------------------
# Password hashing — Argon2id via argon2-cffi (actively maintained, the
# current OWASP-recommended default). No custom cryptography.
# ---------------------------------------------------------------------------

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a plaintext password. Never store the input to this function anywhere."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Constant-time-safe verification; returns False (not an exception) on any mismatch/corruption."""
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
