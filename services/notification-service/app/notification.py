import logging


logger = logging.getLogger("finsightx-notification")


def generate_notification(
    transaction_id: str,
    customer_id: str,
    risk_level: str,
    risk_score: int,
    reasons: list[str],
) -> dict:

    normalized_risk_level = risk_level.upper()

    if normalized_risk_level == "HIGH":
        notification_type = "HIGH_RISK_ALERT"
        priority = "URGENT"
        message = (
            "High-risk transaction detected. "
            f"Transaction ID: {transaction_id}"
        )

    elif normalized_risk_level == "MEDIUM":
        notification_type = "FRAUD_REVIEW_ALERT"
        priority = "HIGH"
        message = (
            "Transaction requires fraud review. "
            f"Transaction ID: {transaction_id}"
        )

    else:
        notification_type = "TRANSACTION_NOTIFICATION"
        priority = "NORMAL"
        message = (
            "Transaction completed risk assessment. "
            f"Transaction ID: {transaction_id}"
        )

    notification = {
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "notification_type": notification_type,
        "priority": priority,
        "risk_level": normalized_risk_level,
        "risk_score": risk_score,
        "message": message,
        "reasons": reasons,
    }

    logger.info(
        "NOTIFICATION GENERATED | "
        "type=%s | "
        "priority=%s | "
        "transaction_id=%s",
        notification_type,
        priority,
        transaction_id,
    )

    return notification