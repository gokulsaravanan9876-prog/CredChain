import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from ..models.enums import JobEmploymentType, JobStatus


class CreateJobBody(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    location: str | None = Field(default=None, max_length=255)
    employment_type: JobEmploymentType
    required_degree: str | None = Field(default=None, max_length=255)
    minimum_cgpa: float | None = None
    graduation_year_requirement: int | None = None
    required_skills: list[str] = Field(default_factory=list)
    required_certifications: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    application_deadline: datetime | None = None


class UpdateJobBody(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    location: str | None = Field(default=None, max_length=255)
    employment_type: JobEmploymentType | None = None
    required_degree: str | None = Field(default=None, max_length=255)
    minimum_cgpa: float | None = None
    graduation_year_requirement: int | None = None
    required_skills: list[str] | None = None
    required_certifications: list[str] | None = None
    required_documents: list[str] | None = None
    application_deadline: datetime | None = None


class EligibilityCheckItem(BaseModel):
    label: str
    met: bool
    mandatory: bool
    # Distinguishes "the student's real data fails this requirement" from
    # "the student has no data to check this requirement against at all" —
    # e.g. a missing CGPA is INCOMPLETE, never silently treated the same as
    # a CGPA that's simply too low. `met` stays a plain bool (True only for
    # "met") for every existing caller; `status` is the richer signal.
    status: Literal["met", "not_met", "incomplete"] = "met"


class EligibilityResult(BaseModel):
    is_eligible: bool
    checks: list[EligibilityCheckItem]
    # ELIGIBLE only when every mandatory check is met with real data.
    # NOT_ELIGIBLE when a mandatory check has real data that fails the
    # requirement. INCOMPLETE when no mandatory check fails outright, but at
    # least one mandatory requirement has no student data to evaluate —
    # never silently reported as eligible OR flatly "not eligible" in that
    # case, since neither claim is actually true yet.
    status: Literal["eligible", "not_eligible", "incomplete"] = "eligible"


class JobResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    title: str
    description: str
    location: str | None
    employment_type: JobEmploymentType
    required_degree: str | None
    minimum_cgpa: float | None
    graduation_year_requirement: int | None
    required_skills: list[str]
    required_certifications: list[str]
    required_documents: list[str]
    status: JobStatus
    application_deadline: datetime | None
    created_at: datetime
    # Populated only on student-facing endpoints (None for the owning
    # company's own views) — computed fresh every time by
    # eligibility_service.evaluate, never AI, never cached against stale data.
    eligibility: EligibilityResult | None = None
