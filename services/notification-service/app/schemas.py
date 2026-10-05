from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FraudAssessedEvent(BaseModel):
    event_type: str
    event_version: str
    event_id: UUID

    transaction_id: UUID
    customer_id: UUID

    risk_level: str
    risk_score: int

    reasons: list[Any] = []

    assessed_at: datetime

    ml_prediction: str | None = None
    ml_probability: float | None = None
    ml_risk_level: str | None = None
    ml_model_version: str | None = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    event_id: UUID
    transaction_id: UUID
    customer_id: UUID

    notification_type: str
    channel: str
    priority: str
    risk_level: str

    title: str
    message: str

    status: str
    risk_score: int

    reasons: list[Any]

    ml_prediction: str | None
    ml_probability: float | None
    ml_risk_level: str | None
    ml_model_version: str | None

    occurred_at: datetime
    created_at: datetime