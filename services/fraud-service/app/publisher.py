import json
import logging
import os
from datetime import datetime, timezone

from kafka import KafkaProducer

from app.database import save_fraud_assessment
from app.metrics import (
    record_fraud_assessment,
    record_ml_prediction,
)


logger = logging.getLogger(
    "finsightx-fraud"
)


KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "kafka:9092",
)

FRAUD_ASSESSED_TOPIC = "fraud.assessed"


producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda value: json.dumps(
        value
    ).encode("utf-8"),
)


def publish_fraud_assessment(
    event: dict,
    risk_level: str,
    risk_score: int,
    reasons: list[str],
    ml_assessment: dict,
) -> None:

    transaction = event["transaction"]

    # ---------------------------------------------------------
    # Persist assessment.
    # ---------------------------------------------------------
    save_fraud_assessment(
        event=event,
        risk_level=risk_level,
        risk_score=risk_score,
        reasons=reasons,
        ml_assessment=ml_assessment,
    )

    # ---------------------------------------------------------
    # Record Prometheus metrics.
    # ---------------------------------------------------------
    record_fraud_assessment(
        risk_level=risk_level
    )

    record_ml_prediction(
        prediction=ml_assessment["prediction"],
        risk_level=ml_assessment["risk_level"],
    )

    logger.info(
        "FRAUD ASSESSMENT STORED | "
        "transaction_id=%s | "
        "rule_risk=%s | "
        "rule_score=%s | "
        "ml_prediction=%s | "
        "ml_probability=%.6f",
        transaction["id"],
        risk_level,
        risk_score,
        ml_assessment["prediction"],
        ml_assessment["fraud_probability"],
    )

    # ---------------------------------------------------------
    # Build fraud.assessed event.
    # ---------------------------------------------------------
    fraud_event = {
        "event_type": "fraud.assessed",
        "event_version": "2.0",
        "event_id": event["event_id"],
        "occurred_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "transaction": {
            "id": transaction["id"],
            "customer_id": transaction[
                "customer_id"
            ],
            "amount": transaction["amount"],
            "currency": transaction["currency"],
            "merchant_name": transaction[
                "merchant_name"
            ],
            "merchant_category": transaction.get(
                "merchant_category"
            ),
            "location": transaction.get(
                "location"
            ),
            "device_id": transaction.get(
                "device_id"
            ),
            "status": transaction.get(
                "status",
                "PENDING",
            ),
        },
        "fraud_assessment": {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "reasons": reasons,
            "rule_based": {
                "risk_level": risk_level,
                "risk_score": risk_score,
            },
            "machine_learning": {
                "model_name": ml_assessment[
                    "model_name"
                ],
                "model_version": ml_assessment[
                    "model_version"
                ],
                "prediction": ml_assessment[
                    "prediction"
                ],
                "fraud_probability": ml_assessment[
                    "fraud_probability"
                ],
                "legitimate_probability": ml_assessment[
                    "legitimate_probability"
                ],
                "risk_level": ml_assessment[
                    "risk_level"
                ],
                "threshold": ml_assessment[
                    "model_threshold"
                ],
            },
        },
    }

    # ---------------------------------------------------------
    # Publish fraud.assessed.
    # ---------------------------------------------------------
    try:

        future = producer.send(
            FRAUD_ASSESSED_TOPIC,
            key=transaction[
                "id"
            ].encode("utf-8"),
            value=fraud_event,
        )

        metadata = future.get(
            timeout=10
        )

        producer.flush()

        logger.info(
            "FRAUD EVENT PUBLISHED | "
            "topic=%s | "
            "partition=%s | "
            "offset=%s | "
            "transaction_id=%s | "
            "rule_risk=%s | "
            "ml_prediction=%s",
            metadata.topic,
            metadata.partition,
            metadata.offset,
            transaction["id"],
            risk_level,
            ml_assessment["prediction"],
        )

    except Exception:

        logger.exception(
            "FAILED TO PUBLISH FRAUD EVENT | "
            "transaction_id=%s",
            transaction["id"],
        )

        raise