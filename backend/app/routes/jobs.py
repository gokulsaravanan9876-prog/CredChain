import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.job import JobResponse
from ..security.permissions import require_student
from ..services import job_service

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=list[JobResponse], summary="List real, currently-open jobs — honest empty state if none exist")
def list_open_jobs(
    search: str | None = Query(default=None, description="Matches job title or description"),
    company_id: uuid.UUID | None = Query(default=None, description="Restrict to one company's open jobs — e.g. a company's profile page"),
    location: str | None = Query(default=None),
    degree: str | None = Query(default=None, description="Matches the job's required_degree"),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> list[JobResponse]:
    if current_user.student is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No student profile for this account")
    jobs = job_service.list_open_jobs(db, search=search, company_id=company_id, location=location, degree=degree)
    return [job_service.to_response(j, student=current_user.student, db=db) for j in jobs]


@router.get("/{job_id}", response_model=JobResponse, summary="View one open job — or a closed one the student has already applied to")
def get_job(job_id: uuid.UUID, current_user: User = Depends(require_student), db: Session = Depends(get_db)) -> JobResponse:
    if current_user.student is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No student profile for this account")
    try:
        job = job_service.get_open_job_or_applied(db, job_id, current_user.student)
    except job_service.JobNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job_service.to_response(job, student=current_user.student, db=db)
