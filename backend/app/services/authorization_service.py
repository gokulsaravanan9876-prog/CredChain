# ---------------------------------------------------------------------------
# The verifier authorization boundary — the ONE function that decides
# whether a given company may see a given credential.
#
# PHASE BOUNDARY: this only ever READS the share_grants / share_grant_credentials
# tables (already part of the Phase 2 schema). Phase 6 owns everything about
# *creating* ShareGrant rows — credential requests, the student's selective
# sharing flow, QR/link generation, secure token issuance. None of that
# exists yet. Because this function's contract is just "does an active grant
# exist for (company, credential)", Phase 6 can start writing ShareGrant rows
# through its own new endpoints and this function keeps working unmodified —
# verification never needs to change when sharing is built.
# ---------------------------------------------------------------------------

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models.company import Company
from ..models.credential import Credential
from ..models.enums import SharePermission
from ..models.share_grant import ShareGrant, ShareGrantCredential


def get_active_share_grant(db: Session, company: Company, credential: Credential) -> ShareGrant | None:
    """
    Returns the active (not revoked, not expired) ShareGrant giving
    `company` access to `credential`, or None. Ordered by created_at desc:
    nothing stops a company being granted the same credential more than
    once (e.g. two separate requests both approved), and since Phase G
    grants can now differ in `permission`, which one "wins" is no longer
    cosmetic — always the most recent grant, reflecting the student's
    latest sharing decision.
    """
    now = datetime.now(timezone.utc)
    return (
        db.query(ShareGrant)
        .join(ShareGrantCredential, ShareGrantCredential.share_grant_id == ShareGrant.id)
        .filter(
            ShareGrant.company_id == company.id,
            ShareGrantCredential.credential_id == credential.id,
            ShareGrant.revoked_at.is_(None),
            ShareGrant.expires_at > now,
        )
        .order_by(ShareGrant.created_at.desc())
        .first()
    )


def is_verifier_authorized(db: Session, company: Company, credential: Credential) -> bool:
    return get_active_share_grant(db, company, credential) is not None


def has_download_permission(db: Session, company: Company, credential: Credential) -> bool:
    """
    True if ANY active grant for (company, credential) permits download —
    not just whichever single grant get_active_share_grant happens to
    return. Nothing stops a company being granted the same credential more
    than once (e.g. two separate approved requests); if any of those active
    grants allows download, download is allowed. Avoids needing a
    deterministic tie-break between grants with identical timestamps.
    """
    now = datetime.now(timezone.utc)
    return (
        db.query(ShareGrant)
        .join(ShareGrantCredential, ShareGrantCredential.share_grant_id == ShareGrant.id)
        .filter(
            ShareGrant.company_id == company.id,
            ShareGrantCredential.credential_id == credential.id,
            ShareGrant.revoked_at.is_(None),
            ShareGrant.expires_at > now,
            ShareGrant.permission == SharePermission.VIEW_DOWNLOAD,
        )
        .first()
        is not None
    )
