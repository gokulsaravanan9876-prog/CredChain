from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.activity import ActivityResponse
from ..security.permissions import require_institution, require_student, require_verifier
from ..services import activity_service

router = APIRouter(tags=["activity"])


@router.get(
    "/api/students/me/activity",
    response_model=list[ActivityResponse],
    summary="The authenticated student's own activity feed, newest first",
)
def student_activity(
    limit: int = Query(default=50, ge=1, le=50),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> list[ActivityResponse]:
    if current_user.student is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No student profile for this account")

    logs = activity_service.get_student_activity(db, current_user.student, limit=limit)
    return [
        ActivityResponse(
            id=log.id,
            action=log.action,
            message=activity_service.render_message(db, log, viewer_role="student"),
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get(
    "/api/institutions/me/activity",
    response_model=list[ActivityResponse],
    summary="The authenticated institution's own activity feed, newest first",
)
def institution_activity(
    limit: int = Query(default=50, ge=1, le=50),
    current_user: User = Depends(require_institution),
    db: Session = Depends(get_db),
) -> list[ActivityResponse]:
    if current_user.institution is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No institution profile for this account")

    logs = activity_service.get_institution_activity(db, current_user.institution, limit=limit)
    return [
        ActivityResponse(
            id=log.id,
            action=log.action,
            message=activity_service.render_message(db, log, viewer_role="institution"),
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get(
    "/api/companies/me/activity",
    response_model=list[ActivityResponse],
    summary="The authenticated company/verifier's own activity feed, newest first",
)
def company_activity(
    limit: int = Query(default=50, ge=1, le=50),
    current_user: User = Depends(require_verifier),
    db: Session = Depends(get_db),
) -> list[ActivityResponse]:
    if current_user.company is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No company profile for this account")

    logs = activity_service.get_company_activity(db, current_user.company, limit=limit)
    return [
        ActivityResponse(
            id=log.id,
            action=log.action,
            message=activity_service.render_message(db, log, viewer_role="company"),
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            created_at=log.created_at,
        )
        for log in logs
    ]
