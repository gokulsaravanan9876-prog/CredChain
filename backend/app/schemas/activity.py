import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityResponse(BaseModel):
    """
    Read-only projection of an ActivityLog row for a role's own activity feed.
    Deliberately excludes actor_user_id and metadata_ — those can carry
    internal ids/context not meant for direct client exposure; `message` is
    the pre-rendered human-readable summary built server-side instead.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    action: str
    message: str
    entity_type: str | None
    entity_id: uuid.UUID | None
    created_at: datetime
