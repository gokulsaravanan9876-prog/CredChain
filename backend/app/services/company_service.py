from sqlalchemy.orm import Session

from ..models.company import Company
from ..schemas.company import UpdateCompanyProfileBody


def list_companies(db: Session) -> list[Company]:
    return db.query(Company).order_by(Company.name).all()


def update_profile(db: Session, company: Company, payload: UpdateCompanyProfileBody) -> Company:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(company, field, value)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company
