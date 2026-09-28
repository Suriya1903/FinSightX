import json
import logging
import os
import threading
import time

from kafka import KafkaConsumer
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import AuditEvent


logger = logging.getLogger("finsightx-audit")


KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "kafka:9092",
)

KAFKA_TOPIC = os.getenv(
    "KAFKA_TOPIC",
    "transaction.created",
)

KAFKA_GROUP_ID = os.getenv(
    "KAFKA_GROUP_ID",
    "finsightx-audit-service",
)

KAFKA_RETRY_DELAY_SECONDS = int(
    os.getenv(
        "KAFKA_RETRY_DELAY_SECONDS",
        "5",
    )
)


def process_event(event: dict) -> None:
    event_id = event.get("event_id")
    event_type = event.get("event_type")
    transaction = event.get("transaction", {})

    if not event_id:
        logger.error(
            "Event does not contain event_id."
        )
        return

    if not transaction.get("id"):
        logger.error(
            "Event %s does not contain transaction.id.",
            event_id,
        )
        return

    db = SessionLocal()

    try:
        existing_event = (
            db.query(AuditEvent)
            .filter(
                AuditEvent.event_id == event_id
            )
            .first()
        )

        if existing_event:
            logger.info(
                "Event %s already processed. Skipping.",
                event_id,
            )
            return

        audit_event = AuditEvent(
            event_id=event_id,
            event_type=event_type or "UNKNOWN",
            transaction_id=str(
                transaction.get("id")
            ),
            customer_id=str(
                transaction.get("customer_id")
            ),
            amount=str(
                transaction.get("amount")
            ),
            currency=str(
                transaction.get("currency")
            ),
            merchant_name=str(
                transaction.get("merchant_name")
            ),
            payload=json.dumps(event),
        )

        db.add(audit_event)
        db.commit()

        logger.info(
            "AUDIT EVENT STORED | event_id=%s | transaction_id=%s",
            event_id,
            transaction.get("id"),
        )

    except IntegrityError:
        db.rollback()

        logger.info(
            "Event %s already exists.",
            event_id,
        )

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to process event %s.",
            event_id,
        )

    finally:
        db.close()


def create_consumer() -> KafkaConsumer:
    logger.info(
        "Connecting to Kafka | bootstrap_servers=%s",
        KAFKA_BOOTSTRAP_SERVERS,
    )

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda value: json.loads(
            value.decode("utf-8")
        ),
    )

    logger.info(
        "Connected to Kafka topic '%s' with group '%s'.",
        KAFKA_TOPIC,
        KAFKA_GROUP_ID,
    )

    return consumer


def consume_events() -> None:
    logger.info(
        "Starting resilient Kafka consumer..."
    )

    while True:
        consumer = None

        try:
            consumer = create_consumer()

            for message in consumer:
                logger.info(
                    "Received event | topic=%s | partition=%s | offset=%s",
                    message.topic,
                    message.partition,
                    message.offset,
                )

                process_event(message.value)

        except Exception:
            logger.exception(
                "Kafka consumer failed. "
                "Retrying in %s seconds...",
                KAFKA_RETRY_DELAY_SECONDS,
            )

        finally:
            if consumer is not None:
                try:
                    consumer.close()
                    logger.info(
                        "Kafka consumer connection closed."
                    )
                except Exception:
                    logger.exception(
                        "Error while closing Kafka consumer."
                    )

        time.sleep(
            KAFKA_RETRY_DELAY_SECONDS
        )


def start_consumer_thread() -> threading.Thread:
    thread = threading.Thread(
        target=consume_events,
        daemon=True,
        name="kafka-consumer",
    )

    thread.start()

    return thread