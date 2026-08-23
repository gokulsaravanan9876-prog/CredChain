from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .common import TimestampMixin, UUIDPrimaryKeyMixin
from .enums import JobEmploymentType, JobStatus

if TYPE_CHECKING:
    from .company import Company
    from .job_application import JobApplication


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A real job posting owned by exactly one Company. required_degree is
    free text matched the same way credential_matcher.py already matches
    job-requirement text against a student's Credential.degree — no new
    matching vocabulary invented. required_documents uses the SAME
    free-text label vocabulary as CredentialRequest.requested_credentials
    (e.g. "Transcript", "Migration Certificate") specifically so that
    applying to a job can drive the existing CredentialRequest/ShareGrant/
    verification_service.check_type_mismatch pipeline unchanged — see
    job_application_service.py.
    """

    __tablename__ = "jobs"
    __table_args__ = (Index("ix_jobs_company_status", "company_id", "status"),)

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[JobEmploymentType] = mapped_column(
        SAEnum(JobEmploymentType, values_callable=lambda e: [m.value for m in e], name="job_employment_type"),
        nullable=False,
    )

    required_degree: Mapped[str | None] = mapped_column(String(255), nullable=True)
    minimum_cgpa: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    graduation_year_requirement: Mapped[int | None] = mapped_column(Integer, nullable=True)
    required_skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    required_certifications: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    required_documents: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, values_callable=lambda e: [m.value for m in e], name="job_status"),
        nullable=False,
        default=JobStatus.DRAFT,
        index=True,
    )
    application_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    company: Mapped[Company] = relationship(back_populates="jobs")
    applications: Mapped[list[JobApplication]] = relationship(back_populates="job")
