import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from app.core.kafka import get_kafka_producer


TRANSACTION_CREATED_TOPIC = "transaction.created"


class EventService:

    @staticmethod
    def publish_transaction_created(
        transaction_id: UUID,
        customer_id: UUID,
        amount: Decimal,
        currency: str,
        merchant_name: str,
        merchant_category: str | None,
        location: str | None,
        device_id: str | None,
        status: str,
    ) -> None:

        event = {
            "event_type": "transaction.created",
            "event_version": "1.0",
            "event_id": str(transaction_id),
            "occurred_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "transaction": {
                "id": str(transaction_id),
                "customer_id": str(customer_id),
                "amount": float(amount),
                "currency": currency,
                "merchant_name": merchant_name,
                "merchant_category": merchant_category,
                "location": location,
                "device_id": device_id,
                "status": status,
            },
        }

        event_json = json.dumps(event)

        producer = get_kafka_producer()

        future = producer.send(
            TRANSACTION_CREATED_TOPIC,
            key=str(transaction_id).encode("utf-8"),
            value=event_json,
        )

        future.get(timeout=10)

        producer.flush()