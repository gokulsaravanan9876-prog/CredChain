from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.enums import UserRole
from ..models.user import User
from ..schemas.notifications import NotificationCounts
from ..security.permissions import get_current_user
from ..services import notification_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get(
    "/me/counts",
    response_model=NotificationCounts,
    summary="Real, role-scoped pending-action counts for the authenticated user — never a hardcoded number",
)
def get_my_notification_counts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> NotificationCounts:
    if current_user.role == UserRole.STUDENT:
        if current_user.student is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No student profile for this account")
        return notification_service.student_counts(db, current_user.student)
    if current_user.role == UserRole.INSTITUTION:
        if current_user.institution is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No institution profile for this account")
        return notification_service.institution_counts(db, current_user.institution)
    if current_user.company is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No company profile for this account")
    return notification_service.company_counts(db, current_user.company)
