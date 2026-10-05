from __future__ import annotations

import json
import logging
import os
import time

from kafka import KafkaConsumer

from app.metrics import (
    observe_fraud_processing_duration,
    record_fraud_event_processed,
    record_fraud_processing_failure,
    record_ml_prediction_failure,
)
from app.ml_client import calculate_time_features, predict_fraud
from app.publisher import publish_fraud_assessment
from app.redis_client import (
    get_redis,
    is_event_processed,
    mark_event_processed,
)
from app.reliability import process_with_retry
from app.rules import assess_transaction
from app.velocity import record_transaction


logger = logging.getLogger("finsightx-fraud")


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
    2. Calculate transaction velocity using Redis.
    3. Run rule-based fraud detection.
    4. Call the ML Service.
    5. Persist fraud assessment in PostgreSQL.
    6. Publish fraud.assessed to Kafka.
    7. Mark the source event as processed.
    """

    event_id = event.get("event_id")

    if not event_id:
        raise ValueError("Event does not contain event_id.")

    # ---------------------------------------------------------
    # Idempotency check.
    # ---------------------------------------------------------
    if is_event_processed(event_id):
        logger.info(
            "IDEMPOTENCY | event_id=%s already processed. Skipping.",
            event_id,
        )
        return

    transaction = event.get(
        "transaction",
        {},
    )

    transaction_id = transaction.get("id")
    customer_id = transaction.get("customer_id")

    amount = float(
        transaction.get(
            "amount",
            0,
        )
    )

    if not transaction_id:
        raise ValueError("Transaction ID is missing.")

    if not customer_id:
        raise ValueError("Customer ID is missing.")

    # ---------------------------------------------------------
    # Redis velocity tracking.
    # ---------------------------------------------------------
    velocity = record_transaction(
        redis_client=redis_client,
        customer_id=customer_id,
        transaction_id=transaction_id,
        amount=amount,
    )

    logger.info(
        "VELOCITY | customer_id=%s | transactions=%s | total_amount=%s",
        customer_id,
        velocity["transaction_count"],
        velocity["total_amount"],
    )

    # ---------------------------------------------------------
    # Rule-based fraud assessment.
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
        "RULE ASSESSMENT | transaction_id=%s | risk=%s | score=%s",
        transaction_id,
        rule_assessment.risk_level,
        rule_assessment.risk_score,
    )

    # ---------------------------------------------------------
    # Time features for ML.
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
    # Machine-learning prediction.
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
        record_ml_prediction_failure()

        logger.exception(
            "ML prediction failed | transaction_id=%s",
            transaction_id,
        )

        raise RuntimeError(
            f"ML fraud prediction failed: {exc}"
        ) from exc

    logger.info(
        "ML ASSESSMENT | transaction_id=%s | prediction=%s | "
        "probability=%.6f | risk=%s",
        transaction_id,
        ml_assessment["prediction"],
        ml_assessment["fraud_probability"],
        ml_assessment["risk_level"],
    )

    # ---------------------------------------------------------
    # Combine rule + ML reasons.
    # ---------------------------------------------------------
    reasons = list(
        rule_assessment.reasons
    )

    reasons.append(
        "ML model prediction: "
        f"{ml_assessment['prediction']} with fraud probability "
        f"{ml_assessment['fraud_probability']:.2%}."
    )

    reasons.append(
        "ML model risk level: "
        f"{ml_assessment['risk_level']} "
        f"(model version "
        f"{ml_assessment['model_version']})."
    )

    # ---------------------------------------------------------
    # Persist and publish fraud assessment.
    # ---------------------------------------------------------
    publish_fraud_assessment(
        event=event,
        risk_level=rule_assessment.risk_level,
        risk_score=rule_assessment.risk_score,
        reasons=reasons,
        ml_assessment=ml_assessment,
    )

    # ---------------------------------------------------------
    # Mark event as successfully processed.
    # ---------------------------------------------------------
    mark_event_processed(event_id)

    logger.info(
        "IDEMPOTENCY | event_id=%s marked as processed.",
        event_id,
    )


def consume_events() -> None:
    """
    Start the Kafka consumer and process transaction events.
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
        value_deserializer=lambda value: json.loads(
            value.decode("utf-8")
        ),
    )

    logger.info(
        "Connected to Kafka topic '%s' with group '%s'.",
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
            "Received transaction event | partition=%s | offset=%s",
            message.partition,
            message.offset,
        )

        event_id = event.get(
            "event_id",
            "unknown",
        )

        start_time = time.perf_counter()

        success = process_with_retry(
            event=event,
            processor=lambda: process_event(
                event,
                redis_client,
            ),
        )

        duration_seconds = (
            time.perf_counter()
            - start_time
        )

        observe_fraud_processing_duration(
            duration_seconds
        )

        if success:

            record_fraud_event_processed(
                status="success"
            )

            logger.info(
                "EVENT PIPELINE SUCCESS | event_id=%s",
                event_id,
            )

        else:

            record_fraud_event_processed(
                status="failed"
            )

            record_fraud_processing_failure()

            logger.error(
                "EVENT PIPELINE FAILED | event_id=%s | sent to DLQ",
                event_id,
            )