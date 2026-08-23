# ---------------------------------------------------------------------------
# JWT issuance/verification. Secret/algorithm/expiry all come from
# app.config.settings (i.e. from .env) — never hardcoded here.
# ---------------------------------------------------------------------------

import uuid
from datetime import datetime, timedelta, timezone

import jwt

from ..config import settings


def create_access_token(*, subject: uuid.UUID, role: str, expires_delta: timedelta | None = None) -> str:
    """Mints a JWT with sub=user id, role=user role, timezone-aware iat/exp."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {
        "sub": str(subject),
        "role": role,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """Returns the decoded payload, or None if the token is malformed, has an invalid signature, or is expired."""
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
