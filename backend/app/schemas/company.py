import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CompanyProfileResponse(BaseModel):
    """A real company's public profile — every field here is a genuine database column, never fabricated placeholder text."""

    id: uuid.UUID
    name: str
    industry: str | None
    website: str | None
    description: str | None
    location: str | None
    company_size: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateCompanyProfileBody(BaseModel):
    """All optional — a PATCH-style update. Only the authenticated company's own row is ever touched (see routes/companies.py)."""

    industry: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    location: str | None = Field(default=None, max_length=255)
    company_size: str | None = Field(default=None, max_length=50)
