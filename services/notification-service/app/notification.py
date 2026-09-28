import logging


logger = logging.getLogger("finsightx-notification")


def generate_notification(
    transaction_id: str,
    customer_id: str,
    risk_level: str,
    risk_score: int,
    reasons: list[str],
) -> dict:

    if risk_level == "HIGH":
        notification_type = "HIGH_RISK_ALERT"
        priority = "URGENT"
        message = (
            f"High-risk transaction detected. "
            f"Transaction ID: {transaction_id}"
        )

    elif risk_level == "MEDIUM":
        notification_type = "FRAUD_REVIEW_ALERT"
        priority = "HIGH"
        message = (
            f"Transaction requires fraud review. "
            f"Transaction ID: {transaction_id}"
        )

    else:
        notification_type = "TRANSACTION_NOTIFICATION"
        priority = "NORMAL"
        message = (
            f"Transaction completed risk assessment. "
            f"Transaction ID: {transaction_id}"
        )

    notification = {
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "notification_type": notification_type,
        "priority": priority,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "message": message,
        "reasons": reasons,
    }

    logger.info(
        "NOTIFICATION GENERATED | type=%s | priority=%s | transaction_id=%s",
        notification_type,
        priority,
        transaction_id,
    )

    return notification