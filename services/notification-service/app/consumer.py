from __future__ import annotations

import json
import logging
import os

from kafka import KafkaConsumer

from app.notification import generate_notification


logger = logging.getLogger("finsightx-notification")


KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "kafka:9092",
)

KAFKA_TOPIC = os.getenv(
    "KAFKA_TOPIC",
    "fraud.assessed",
)

KAFKA_GROUP_ID = os.getenv(
    "KAFKA_GROUP_ID",
    "finsightx-notification-service",
)


def consume_events() -> None:
    logger.info(
        "Starting notification Kafka consumer..."
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

    for message in consumer:
        try:
            event = message.value

            logger.info(
                "Received fraud assessment | "
                "partition=%s | offset=%s",
                message.partition,
                message.offset,
            )

            transaction = event.get(
                "transaction",
                {},
            )

            assessment = event.get(
                "fraud_assessment",
                {},
            )

            transaction_id = transaction.get(
                "id",
                "unknown",
            )

            customer_id = transaction.get(
                "customer_id",
                "unknown",
            )

            risk_level = assessment.get(
                "risk_level",
                "UNKNOWN",
            )

            risk_score = int(
                assessment.get(
                    "risk_score",
                    0,
                )
            )

            reasons = assessment.get(
                "reasons",
                [],
            )

            notification = generate_notification(
                transaction_id=transaction_id,
                customer_id=customer_id,
                risk_level=risk_level,
                risk_score=risk_score,
                reasons=reasons,
            )

            logger.info(
                "NOTIFICATION READY | %s",
                json.dumps(notification),
            )

        except Exception:
            logger.exception(
                "Failed to process fraud assessment event."
            )