from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone

from kafka import KafkaConsumer
from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import AuditLog
from app.schemas import AuditEvent


logger = logging.getLogger("finsightx.audit")


class AuditConsumer:
    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._consume,
            name="audit-kafka-consumer",
            daemon=True,
        )

        self._thread.start()

        logger.info(
            "Audit Kafka consumer thread started."
        )

    def stop(self) -> None:
        self._stop_event.set()

        if self._thread:
            self._thread.join(timeout=5)

        logger.info(
            "Audit Kafka consumer stopped."
        )

    def _consume(self) -> None:

        consumer: KafkaConsumer | None = None

        while not self._stop_event.is_set():

            try:

                if consumer is None:

                    logger.info(
                        "Connecting Audit Service to Kafka: %s",
                        settings.KAFKA_BOOTSTRAP_SERVERS,
                    )

                    consumer = KafkaConsumer(
                        settings.KAFKA_TOPIC,
                        bootstrap_servers=(
                            settings.KAFKA_BOOTSTRAP_SERVERS
                        ),
                        group_id=settings.KAFKA_GROUP_ID,
                        auto_offset_reset="earliest",
                        enable_auto_commit=False,
                        value_deserializer=lambda value: (
                            json.loads(
                                value.decode("utf-8")
                            )
                        ),
                    )

                    logger.info(
                        "Audit Service subscribed to topic: %s",
                        settings.KAFKA_TOPIC,
                    )

                records = consumer.poll(
                    timeout_ms=1000,
                )

                for _, messages in records.items():

                    for message in messages:

                        try:
                            self._process_message(
                                message.value
                            )

                            consumer.commit()

                        except Exception:
                            logger.exception(
                                "Failed to process audit event."
                            )

            except Exception:
                logger.exception(
                    "Audit Kafka consumer error. Retrying."
                )

                if consumer is not None:

                    try:
                        consumer.close()
                    except Exception:
                        pass

                    consumer = None

                self._stop_event.wait(5)

        if consumer is not None:

            try:
                consumer.close()
            except Exception:
                pass

    @staticmethod
    def _process_message(
        payload: dict,
    ) -> None:

        event = AuditEvent.model_validate(payload)

        with SessionLocal() as db:

            existing = db.scalar(
                select(AuditLog).where(
                    AuditLog.event_id
                    == event.event_id
                )
            )

            if existing is not None:

                logger.info(
                    "Audit event already processed: %s",
                    event.event_id,
                )

                return

            audit_log = AuditLog(
                event_id=event.event_id,
                user_id=event.user_id,
                role=event.role,
                action=event.action,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                result=event.result,
                details=event.details,
                occurred_at=event.occurred_at,
                created_at=datetime.now(timezone.utc),
            )

            db.add(audit_log)
            db.commit()

            logger.info(
                "AUDIT EVENT STORED | event_id=%s "
                "user_id=%s role=%s action=%s "
                "resource=%s/%s result=%s",
                event.event_id,
                event.user_id,
                event.role,
                event.action,
                event.resource_type,
                event.resource_id,
                event.result,
            )


audit_consumer = AuditConsumer()