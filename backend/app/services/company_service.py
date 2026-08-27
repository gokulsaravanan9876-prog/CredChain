from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models.company import Company
from ..models.enums import JobStatus
from ..models.job import Job
from ..schemas.company import CompanyProfileResponse, UpdateCompanyProfileBody


def list_companies(db: Session, *, search: str | None = None, industry: str | None = None, location: str | None = None) -> list[Company]:
    """
    Public company directory listing. search matches name/industry/location
    (case-insensitive substring, same approach as institution_service.list_institutions);
    industry/location are exact-match filters over whatever free-text value
    the company/seed data actually has — there is no fixed industry/location
    vocabulary to validate against.
    """
    query = db.query(Company)
    if search:
        needle = f"%{search.strip()}%"
        query = query.filter(
            or_(Company.name.ilike(needle), Company.industry.ilike(needle), Company.location.ilike(needle))
        )
    if industry:
        query = query.filter(Company.industry.ilike(industry.strip()))
    if location:
        query = query.filter(Company.location.ilike(f"%{location.strip()}%"))
    return query.order_by(Company.name).all()


def _open_job_count(db: Session, company_id) -> int:
    return db.query(func.count(Job.id)).filter(Job.company_id == company_id, Job.status == JobStatus.OPEN).scalar() or 0


def to_response(db: Session, company: Company) -> CompanyProfileResponse:
    return CompanyProfileResponse(
        id=company.id,
        name=company.name,
        industry=company.industry,
        website=company.website,
        description=company.description,
        location=company.location,
        company_size=company.company_size,
        created_at=company.created_at,
        open_positions_count=_open_job_count(db, company.id),
    )


def update_profile(db: Session, company: Company, payload: UpdateCompanyProfileBody) -> Company:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(company, field, value)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company
