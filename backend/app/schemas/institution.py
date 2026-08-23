import uuid

from pydantic import BaseModel


class InstitutionSummaryResponse(BaseModel):
    """
    Public-safe institution listing — used by a student choosing which
    institution to link during registration or afterward. Deliberately
    excludes registration_number and public_key: nothing here is sensitive
    (institution id/name are already visible on every credential a student
    or verifier sees), but there's no reason to expose more than a name to
    pick from.
    """

    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}
