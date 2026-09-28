from __future__ import annotations

import json
import logging
import os

from kafka import KafkaConsumer

from app.ml_client import (
    calculate_time_features,
    predict_fraud,
)
from app.publisher import publish_fraud_assessment
from app.redis_client import (
    get_redis,
    is_event_processed,
    mark_event_processed,
)
from app.reliability import process_with_retry
from app.rules import assess_transaction
from app.velocity import record_transaction


logger = logging.getLogger(
    "finsightx-fraud"
)


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
    "finsightx-fraud-service",
)


def process_event(
    event: dict,
    redis_client,
) -> None:
    """
    Process one transaction.created event.

    Processing flow:

    1. Check idempotency.
    2. Calculate Redis transaction velocity.
    3. Run existing rule-based fraud engine.
    4. Call ML fraud model.
    5. Persist combined assessment.
    6. Publish fraud.assessed.
    7. Mark source event processed.
    """

    event_id = event.get(
        "event_id"
    )

    if not event_id:
        raise ValueError(
            "Event does not contain event_id."
        )

    if is_event_processed(
        event_id
    ):
        logger.info(
            "IDEMPOTENCY | event_id=%s "
            "already processed. Skipping.",
            event_id,
        )
        return

    transaction = event.get(
        "transaction",
        {},
    )

    transaction_id = transaction.get(
        "id"
    )

    customer_id = transaction.get(
        "customer_id"
    )

    amount = float(
        transaction.get(
            "amount",
            0,
        )
    )

    if not transaction_id:
        raise ValueError(
            "Transaction ID is missing."
        )

    if not customer_id:
        raise ValueError(
            "Customer ID is missing."
        )

    # ---------------------------------------------------------
    # Redis velocity
    # ---------------------------------------------------------

    velocity = record_transaction(
        redis_client=redis_client,
        customer_id=customer_id,
        transaction_id=transaction_id,
        amount=amount,
    )

    logger.info(
        "VELOCITY | customer_id=%s | "
        "transactions=%s | total_amount=%s",
        customer_id,
        velocity["transaction_count"],
        velocity["total_amount"],
    )

    # ---------------------------------------------------------
    # Existing rule-based fraud engine
    # ---------------------------------------------------------

    rule_assessment = assess_transaction(
        amount=amount,
        merchant_category=transaction.get(
            "merchant_category"
        ),
        location=transaction.get(
            "location"
        ),
        device_id=transaction.get(
            "device_id"
        ),
        velocity_count=velocity[
            "transaction_count"
        ],
        velocity_amount=velocity[
            "total_amount"
        ],
    )

    logger.info(
        "RULE ASSESSMENT | transaction_id=%s | "
        "risk=%s | score=%s",
        transaction_id,
        rule_assessment.risk_level,
        rule_assessment.risk_score,
    )

    # ---------------------------------------------------------
    # ML feature construction
    # ---------------------------------------------------------

    (
        transaction_hour,
        transaction_day_of_week,
        is_weekend,
    ) = calculate_time_features(
        event.get("occurred_at")
    )

    customer_status = transaction.get(
        "customer_status",
        "ACTIVE",
    )

    # ---------------------------------------------------------
    # ML prediction
    # ---------------------------------------------------------

    try:
        ml_assessment = predict_fraud(
            amount=amount,
            merchant_category=transaction.get(
                "merchant_category"
            ),
            currency=transaction.get(
                "currency"
            ),
            transaction_status=transaction.get(
                "status",
                "PENDING",
            ),
            location=transaction.get(
                "location"
            ),
            device_id=transaction.get(
                "device_id"
            ),
            customer_status=customer_status,
            transaction_velocity=velocity[
                "transaction_count"
            ],
            recent_transaction_amount=velocity[
                "total_amount"
            ],
            transaction_hour=transaction_hour,
            transaction_day_of_week=transaction_day_of_week,
            is_weekend=is_weekend,
        )

    except Exception as exc:
        logger.exception(
            "ML prediction failed | "
            "transaction_id=%s",
            transaction_id,
        )

        raise RuntimeError(
            f"ML fraud prediction failed: {exc}"
        ) from exc

    logger.info(
        "ML ASSESSMENT | transaction_id=%s | "
        "prediction=%s | probability=%.6f | risk=%s",
        transaction_id,
        ml_assessment["prediction"],
        ml_assessment["fraud_probability"],
        ml_assessment["risk_level"],
    )

    # ---------------------------------------------------------
    # Combined assessment
    #
    # The existing rule engine remains authoritative for the
    # stored rule-based risk score.
    #
    # ML output is persisted alongside it as additional evidence.
    # ---------------------------------------------------------

    reasons = list(
        rule_assessment.reasons
    )

    reasons.append(
        "ML model prediction: "
        f"{ml_assessment['prediction']} "
        f"with fraud probability "
        f"{ml_assessment['fraud_probability']:.2%}."
    )

    reasons.append(
        "ML model risk level: "
        f"{ml_assessment['risk_level']} "
        f"(model version "
        f"{ml_assessment['model_version']})."
    )

    publish_fraud_assessment(
        event=event,
        risk_level=rule_assessment.risk_level,
        risk_score=rule_assessment.risk_score,
        reasons=reasons,
        ml_assessment=ml_assessment,
    )

    # ---------------------------------------------------------
    # Idempotency
    # ---------------------------------------------------------

    mark_event_processed(
        event_id
    )

    logger.info(
        "IDEMPOTENCY | event_id=%s "
        "marked as processed.",
        event_id,
    )


def consume_events() -> None:
    """
    Continuously consume transaction.created events.
    """

    logger.info(
        "Starting fraud detection Kafka consumer..."
    )

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda value:
            json.loads(
                value.decode("utf-8")
            ),
    )

    logger.info(
        "Connected to Kafka topic '%s' "
        "with group '%s'.",
        KAFKA_TOPIC,
        KAFKA_GROUP_ID,
    )

    redis_client = get_redis()

    try:
        redis_client.ping()

        logger.info(
            "Connected to Redis successfully."
        )

    except Exception:
        logger.exception(
            "Unable to connect to Redis."
        )

    for message in consumer:

        event = message.value

        logger.info(
            "Received transaction event | "
            "partition=%s | offset=%s",
            message.partition,
            message.offset,
        )

        event_id = event.get(
            "event_id",
            "unknown",
        )

        success = process_with_retry(
            event=event,
            processor=lambda: process_event(
                event,
                redis_client,
            ),
        )

        if success:
            logger.info(
                "EVENT PIPELINE SUCCESS | "
                "event_id=%s",
                event_id,
            )

        else:
            logger.error(
                "EVENT PIPELINE FAILED | "
                "event_id=%s | sent to DLQ",
                event_id,
            )