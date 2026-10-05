from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from app.core.kafka import get_kafka_producer


AUDIT_TOPIC = "audit.events"


def publish_audit_event(
    *,
    user_id: str | UUID,
    role: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    result: str = "SUCCESS",
    details: dict[str, Any] | None = None,
) -> str:

    event_id = uuid4()

    event = {
        "event_type": "audit.event",
        "event_version": "1.0",
        "event_id": str(event_id),
        "occurred_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "user_id": str(user_id),
        "role": role,

        "action": action,

        "resource_type": resource_type,
        "resource_id": resource_id,

        "result": result,

        "details": details or {},
    }

    producer = get_kafka_producer()

    future = producer.send(
        AUDIT_TOPIC,
        key=str(user_id).encode("utf-8"),
        value=json.dumps(event),
    )

    future.get(timeout=10)

    producer.flush()

    return str(event_id)