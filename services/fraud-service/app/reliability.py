import json
import logging
import os
import time
from typing import Callable

from kafka import KafkaProducer


logger = logging.getLogger(
    "finsightx-fraud-reliability"
)


KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "kafka:9092",
)

DLQ_TOPIC = os.getenv(
    "KAFKA_DLQ_TOPIC",
    "transaction.created.DLQ",
)

MAX_RETRIES = int(
    os.getenv(
        "KAFKA_MAX_RETRIES",
        "3",
    )
)

RETRY_DELAY_SECONDS = float(
    os.getenv(
        "KAFKA_RETRY_DELAY_SECONDS",
        "1",
    )
)


producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda value: json.dumps(
        value
    ).encode("utf-8"),
)


def publish_to_dlq(
    event: dict,
    error: str,
) -> None:

    dlq_event = {
        "original_event": event,
        "dlq_reason": error,
        "retry_count": MAX_RETRIES,
    }

    future = producer.send(
        DLQ_TOPIC,
        key=str(
            event.get(
                "event_id",
                "unknown",
            )
        ).encode("utf-8"),
        value=dlq_event,
    )

    metadata = future.get(
        timeout=10
    )

    producer.flush()

    logger.error(
        "EVENT SENT TO DLQ | topic=%s | partition=%s | offset=%s | event_id=%s",
        DLQ_TOPIC,
        metadata.partition,
        metadata.offset,
        event.get("event_id"),
    )


def process_with_retry(
    event: dict,
    processor: Callable[[], None],
) -> bool:

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            processor()

            logger.info(
                "EVENT PROCESSED SUCCESSFULLY | event_id=%s | attempt=%s",
                event.get("event_id"),
                attempt,
            )

            return True

        except Exception as exc:

            logger.exception(
                "EVENT PROCESSING FAILED | event_id=%s | attempt=%s/%s",
                event.get("event_id"),
                attempt,
                MAX_RETRIES,
            )

            if attempt < MAX_RETRIES:

                time.sleep(
                    RETRY_DELAY_SECONDS
                )

            else:

                publish_to_dlq(
                    event=event,
                    error=str(exc),
                )

    return False