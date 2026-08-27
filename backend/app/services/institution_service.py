from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models.institution import Institution


def list_institutions(db: Session, *, search: str | None = None, location: str | None = None, country: str | None = None) -> list[Institution]:
    """
    Public institution directory listing (also reused, unchanged in shape,
    by the registration/link-institution picker — see routes/institutions.py).
    search matches name/location (case-insensitive substring); country is a
    substring match over the free-text `location` field rather than a
    separate column, since the seeded/imported data stores location as one
    "City, State, Country"-style string rather than structured parts.
    """
    query = db.query(Institution)
    if search:
        needle = f"%{search.strip()}%"
        query = query.filter(or_(Institution.name.ilike(needle), Institution.location.ilike(needle)))
    if location:
        query = query.filter(Institution.location.ilike(f"%{location.strip()}%"))
    if country:
        query = query.filter(Institution.location.ilike(f"%{country.strip()}%"))
    return query.order_by(Institution.name).all()


def get_institution(db: Session, institution_id: UUID) -> Institution | None:
    return db.get(Institution, institution_id)
