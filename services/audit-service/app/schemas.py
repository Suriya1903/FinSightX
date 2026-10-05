from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditEvent(BaseModel):
    event_type: str
    event_version: str
    event_id: UUID
    occurred_at: datetime

    user_id: UUID
    role: str

    action: str

    resource_type: str
    resource_id: str | None = None

    result: str

    details: dict[str, Any] = {}


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: UUID
    user_id: UUID
    role: str
    action: str
    resource_type: str
    resource_id: str | None
    result: str
    details: dict[str, Any]
    occurred_at: datetime
    created_at: datetime