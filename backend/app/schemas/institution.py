import uuid

from pydantic import BaseModel


class InstitutionSummaryResponse(BaseModel):
    """
    Public-safe institution profile — used both by a student choosing which
    institution to link during registration (name is enough there) and by
    the student Institution Directory/Profile pages (the rest of the
    fields). Deliberately excludes registration_number and public_key:
    neither is sensitive (institution id/name are already visible on every
    credential a student or verifier sees), but there's no reason to expose
    more than the public directory fields below.

    A row with no description/location/website/institution_type is a real
    institution that simply hasn't had those fields filled in yet (or was
    seeded from a dataset that didn't have that field) — rendered as
    "not available", never fabricated.
    """

    id: uuid.UUID
    name: str
    description: str | None = None
    location: str | None = None
    website: str | None = None
    institution_type: str | None = None

    model_config = {"from_attributes": True}
