import json
from datetime import datetime, timezone

from app.kafka import get_kafka_producer


TRANSACTION_CREATED_TOPIC = "transaction.created"


def publish_transaction_created(
    transaction,
) -> None:

    event = {
        "event_type": "transaction.created",
        "event_version": "1.0",
        "event_id": str(transaction.id),
        "occurred_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "transaction": {
            "id": str(transaction.id),
            "customer_id": str(
                transaction.customer_id
            ),
            "amount": float(
                transaction.amount
            ),
            "currency": transaction.currency,
            "merchant_name": transaction.merchant_name,
            "merchant_category": (
                transaction.merchant_category
            ),
            "location": transaction.location,
            "device_id": transaction.device_id,
            "status": transaction.status,
        },
    }

    producer = get_kafka_producer()

    future = producer.send(
        TRANSACTION_CREATED_TOPIC,
        key=str(
            transaction.id
        ).encode("utf-8"),
        value=json.dumps(event),
    )

    metadata = future.get(
        timeout=10
    )

    producer.flush()

    print(
        "TRANSACTION EVENT PUBLISHED | "
        f"topic={metadata.topic} | "
        f"partition={metadata.partition} | "
        f"offset={metadata.offset} | "
        f"transaction_id={transaction.id}"
    )