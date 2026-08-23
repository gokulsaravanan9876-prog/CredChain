from pydantic import BaseModel


class NotificationCounts(BaseModel):
    """
    Role-aware pending-action counts, each a real COUNT(...) query against
    existing status columns — never a fabricated number, never persisted
    read/unread state. See app/services/notification_service.py for exactly
    what each count means and why it's honestly "pending my action" rather
    than a generic unread tally.
    """

    # Student
    pending_company_requests: int | None = None
    # Institution
    pending_certificate_requests: int | None = None
    pending_document_reviews: int | None = None
    # Company/verifier
    unverified_shared_credentials: int | None = None
    new_job_applications: int | None = None
