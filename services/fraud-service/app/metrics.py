from __future__ import annotations

from prometheus_client import Counter, Histogram


FRAUD_EVENTS_PROCESSED_TOTAL = Counter(
    "finsightx_fraud_events_processed_total",
    "Total number of transaction events processed by the Fraud Service.",
    [
        "status",
    ],
)


FRAUD_ASSESSMENTS_TOTAL = Counter(
    "finsightx_fraud_assessments_total",
    "Total number of fraud assessments produced by risk level.",
    [
        "risk_level",
    ],
)


ML_PREDICTIONS_TOTAL = Counter(
    "finsightx_ml_predictions_total",
    "Total number of ML fraud predictions produced.",
    [
        "prediction",
        "risk_level",
    ],
)


FRAUD_PROCESSING_FAILURES_TOTAL = Counter(
    "finsightx_fraud_processing_failures_total",
    "Total number of Fraud Service processing failures.",
)


ML_PREDICTION_FAILURES_TOTAL = Counter(
    "finsightx_ml_prediction_failures_total",
    "Total number of ML prediction failures.",
)


FRAUD_PROCESSING_DURATION_SECONDS = Histogram(
    "finsightx_fraud_processing_duration_seconds",
    "Time spent processing transaction events by the Fraud Service.",
)


def record_fraud_event_processed(
    *,
    status: str,
) -> None:
    FRAUD_EVENTS_PROCESSED_TOTAL.labels(
        status=status,
    ).inc()


def record_fraud_assessment(
    *,
    risk_level: str,
) -> None:
    FRAUD_ASSESSMENTS_TOTAL.labels(
        risk_level=risk_level,
    ).inc()


def record_ml_prediction(
    *,
    prediction: str,
    risk_level: str,
) -> None:
    ML_PREDICTIONS_TOTAL.labels(
        prediction=prediction,
        risk_level=risk_level,
    ).inc()


def record_fraud_processing_failure() -> None:
    FRAUD_PROCESSING_FAILURES_TOTAL.inc()


def record_ml_prediction_failure() -> None:
    ML_PREDICTION_FAILURES_TOTAL.inc()


def observe_fraud_processing_duration(
    duration_seconds: float,
) -> None:
    FRAUD_PROCESSING_DURATION_SECONDS.observe(
        duration_seconds
    )