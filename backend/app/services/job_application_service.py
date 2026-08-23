# ---------------------------------------------------------------------------
# Job applications. Deliberately owns ONLY the application's status
# lifecycle — the actual credential sharing is delegated entirely to the
# existing CredentialRequest + sharing_service.approve_request pipeline
# (Phase 6/PS3-F from prior phases), unmodified. Applying to a job creates a
# real CredentialRequest exactly as if the company had asked for
# job.required_documents directly, then immediately approves it with the
# student's chosen credential_ids via the EXISTING approve_request function
# — same ownership checks, same ShareGrant creation, same
# credential_request_id link that verification_service.check_type_mismatch
# already knows how to read. No second sharing or verification system.
# ---------------------------------------------------------------------------

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models.credential_request import CredentialRequest
from ..models.enums import ApplicationStatus, CredentialRequestStatus, JobStatus, SharePermission
from ..models.job import Job
from ..models.job_application import JobApplication
from ..models.student import Student
from ..schemas.job import EligibilityResult
from ..schemas.job_application import CompanyApplicationResponse, StudentApplicationResponse
from . import eligibility_service, sharing_service

APPLICATION_SHARE_EXPIRY_DAYS = 30


class JobNotFoundError(Exception):
    pass


class JobNotOpenError(Exception):
    pass


class ApplicationDeadlinePassedError(Exception):
    pass


class AlreadyAppliedError(Exception):
    pass


class ApplicationNotFoundError(Exception):
    pass


class ApplicationNotOwnedError(Exception):
    pass


class InvalidStatusTransitionError(Exception):
    pass


class RejectionReasonRequiredError(Exception):
    pass


class WithdrawalNotAllowedError(Exception):
    pass


_ALLOWED_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.APPLIED: {ApplicationStatus.UNDER_REVIEW, ApplicationStatus.REJECTED},
    ApplicationStatus.UNDER_REVIEW: {ApplicationStatus.SHORTLISTED, ApplicationStatus.REJECTED},
    ApplicationStatus.SHORTLISTED: {ApplicationStatus.ACCEPTED, ApplicationStatus.REJECTED},
}


def apply_to_job(
    db: Session,
    student: Student,
    *,
    job_id: uuid.UUID,
    credential_ids: list[uuid.UUID],
) -> JobApplication:
    job = db.get(Job, job_id)
    if job is None:
        raise JobNotFoundError()
    if job.status != JobStatus.OPEN:
        raise JobNotOpenError()
    if job.application_deadline is not None and datetime.now(timezone.utc) > job.application_deadline:
        raise ApplicationDeadlinePassedError()

    existing = (
        db.query(JobApplication)
        .filter(JobApplication.job_id == job.id, JobApplication.student_id == student.id)
        .first()
    )
    if existing is not None:
        raise AlreadyAppliedError()

    # Same shape a company's own direct request takes — this IS that
    # pipeline, not a lookalike of it.
    request = CredentialRequest(
        company_id=job.company_id,
        student_id=student.id,
        purpose=f"Application: {job.title}",
        status=CredentialRequestStatus.PENDING,
        requested_credentials=job.required_documents,
    )
    db.add(request)
    db.flush()

    # Reuses the existing, unmodified approve_request — same ownership
    # checks on credential_ids, same ShareGrant + credential_request_id
    # link that the mismatch/verification pipeline already understands.
    grant, _raw_token = sharing_service.approve_request(
        db,
        student,
        request.id,
        credential_ids=credential_ids,
        expires_in_days=APPLICATION_SHARE_EXPIRY_DAYS,
        permission=SharePermission.VIEW_ONLY,
    )

    application = JobApplication(
        student_id=student.id,
        job_id=job.id,
        company_id=job.company_id,
        status=ApplicationStatus.APPLIED,
        credential_request_id=request.id,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def list_for_student(db: Session, student: Student) -> list[JobApplication]:
    return db.query(JobApplication).filter(JobApplication.student_id == student.id).order_by(JobApplication.created_at.desc()).all()


def list_for_company(db: Session, company_id: uuid.UUID) -> list[JobApplication]:
    return db.query(JobApplication).filter(JobApplication.company_id == company_id).order_by(JobApplication.created_at.desc()).all()


def _get_owned_application(db: Session, company_id: uuid.UUID, application_id: uuid.UUID) -> JobApplication:
    application = db.get(JobApplication, application_id)
    if application is None:
        raise ApplicationNotFoundError()
    if application.company_id != company_id:
        raise ApplicationNotOwnedError()
    return application


def update_status(
    db: Session,
    company_id: uuid.UUID,
    application_id: uuid.UUID,
    new_status: ApplicationStatus,
    *,
    reason: str | None = None,
) -> JobApplication:
    application = _get_owned_application(db, company_id, application_id)
    allowed = _ALLOWED_TRANSITIONS.get(application.status, set())
    if new_status not in allowed:
        raise InvalidStatusTransitionError()
    if new_status == ApplicationStatus.REJECTED and not (reason and reason.strip()):
        raise RejectionReasonRequiredError()

    application.status = new_status
    application.rejection_reason = reason.strip() if new_status == ApplicationStatus.REJECTED else application.rejection_reason
    db.add(application)

    from ..models.activity_log import ActivityLog

    db.add(
        ActivityLog(
            actor_user_id=application.company.user_id,
            action=f"APPLICATION_{new_status.value.upper()}",
            entity_type="job_application",
            entity_id=application.id,
            metadata_={"job_id": str(application.job_id), "student_id": str(application.student_id)}
            | ({"reason": application.rejection_reason} if new_status == ApplicationStatus.REJECTED else {}),
        )
    )

    db.commit()
    db.refresh(application)
    return application


def withdraw_application(db: Session, student: Student, application_id: uuid.UUID) -> JobApplication:
    """Only the owning student may withdraw, and only from a state where the outcome isn't already final — an ACCEPTED offer can't be silently pulled back through this path."""
    application = db.get(JobApplication, application_id)
    if application is None:
        raise ApplicationNotFoundError()
    if application.student_id != student.id:
        raise ApplicationNotOwnedError()
    if application.status not in {ApplicationStatus.APPLIED, ApplicationStatus.UNDER_REVIEW, ApplicationStatus.SHORTLISTED}:
        raise WithdrawalNotAllowedError()

    application.status = ApplicationStatus.WITHDRAWN
    db.add(application)

    from ..models.activity_log import ActivityLog

    db.add(
        ActivityLog(
            actor_user_id=student.user_id,
            action="APPLICATION_WITHDRAWN",
            entity_type="job_application",
            entity_id=application.id,
            metadata_={"job_id": str(application.job_id)},
        )
    )

    db.commit()
    db.refresh(application)
    return application


def to_student_response(application: JobApplication) -> StudentApplicationResponse:
    return StudentApplicationResponse(
        id=application.id,
        job_id=application.job_id,
        job_title=application.job.title,
        company_id=application.company_id,
        company_name=application.company.name,
        status=application.status,
        rejection_reason=application.rejection_reason,
        created_at=application.created_at,
    )


def to_company_response(db: Session, application: JobApplication) -> CompanyApplicationResponse:
    credential_request = None
    if application.credential_request is not None:
        credential_request = sharing_service.to_credential_request_response(db, application.credential_request)

    eligibility = EligibilityResult(**eligibility_service.evaluate(db, application.job, application.student))

    return CompanyApplicationResponse(
        id=application.id,
        job_id=application.job_id,
        job_title=application.job.title,
        student_id=application.student_id,
        student_name=application.student.user.full_name,
        student_identifier=application.student.student_identifier,
        status=application.status,
        rejection_reason=application.rejection_reason,
        created_at=application.created_at,
        credential_request=credential_request,
        eligibility=eligibility,
    )
