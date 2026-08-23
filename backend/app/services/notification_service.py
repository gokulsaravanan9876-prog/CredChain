# ---------------------------------------------------------------------------
# PS3 Phase E: real pending-action counts, computed live from existing
# status columns — no new "unread" tracking table, no fabricated numbers.
# Each count is deliberately scoped to "this needs the viewer's action" (or,
# for the company count, "newly available and not yet verified") so it
# self-clears as a natural side effect of the user acting — approving,
# rejecting, verifying — rather than needing a separate "mark as read" step.
# ---------------------------------------------------------------------------

from datetime import datetime, timezone

from sqlalchemy import not_
from sqlalchemy.orm import Session

from ..models.company import Company
from ..models.credential_request import CredentialRequest
from ..models.enums import ApplicationStatus, CredentialRequestStatus, InstitutionRequestStatus, StudentDocumentStatus
from ..models.institution import Institution
from ..models.institution_certificate_request import InstitutionCertificateRequest
from ..models.job_application import JobApplication
from ..models.share_grant import ShareGrant, ShareGrantCredential
from ..models.student import Student
from ..models.student_document import StudentDocument
from ..models.verification_event import VerificationEvent
from ..schemas.notifications import NotificationCounts


def student_counts(db: Session, student: Student) -> NotificationCounts:
    pending = (
        db.query(CredentialRequest)
        .filter(CredentialRequest.student_id == student.id, CredentialRequest.status == CredentialRequestStatus.PENDING)
        .count()
    )
    return NotificationCounts(pending_company_requests=pending)


def institution_counts(db: Session, institution: Institution) -> NotificationCounts:
    pending_certs = (
        db.query(InstitutionCertificateRequest)
        .filter(
            InstitutionCertificateRequest.institution_id == institution.id,
            InstitutionCertificateRequest.status == InstitutionRequestStatus.PENDING,
        )
        .count()
    )
    pending_docs = (
        db.query(StudentDocument)
        .filter(
            StudentDocument.institution_id == institution.id,
            StudentDocument.status.in_([StudentDocumentStatus.UNVERIFIED, StudentDocumentStatus.UNDER_REVIEW]),
        )
        .count()
    )
    return NotificationCounts(pending_certificate_requests=pending_certs, pending_document_reviews=pending_docs)


def company_counts(db: Session, company: Company) -> NotificationCounts:
    now = datetime.now(timezone.utc)
    verified_credential_ids = db.query(VerificationEvent.credential_id).filter(VerificationEvent.company_id == company.id)
    unverified = (
        db.query(ShareGrantCredential.credential_id)
        .join(ShareGrant, ShareGrant.id == ShareGrantCredential.share_grant_id)
        .filter(
            ShareGrant.company_id == company.id,
            ShareGrant.revoked_at.is_(None),
            ShareGrant.expires_at > now,
            not_(ShareGrantCredential.credential_id.in_(verified_credential_ids)),
        )
        .distinct()
        .count()
    )
    new_applications = (
        db.query(JobApplication)
        .filter(JobApplication.company_id == company.id, JobApplication.status == ApplicationStatus.APPLIED)
        .count()
    )
    return NotificationCounts(unverified_shared_credentials=unverified, new_job_applications=new_applications)
