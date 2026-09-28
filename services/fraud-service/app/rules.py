from dataclasses import dataclass


@dataclass
class FraudAssessment:
    risk_level: str
    risk_score: int
    reasons: list[str]


def assess_transaction(
    amount: float,
    merchant_category: str | None,
    location: str | None,
    device_id: str | None,
    velocity_count: int = 0,
    velocity_amount: float = 0.0,
) -> FraudAssessment:

    risk_score = 0

    reasons: list[str] = []

    # Rule 1: unusually large transaction

    if amount >= 50000:

        risk_score += 60

        reasons.append(
            "Transaction amount is very high."
        )

    elif amount >= 20000:

        risk_score += 30

        reasons.append(
            "Transaction amount is above the normal threshold."
        )

    # Rule 2: potentially higher-risk merchant categories

    high_risk_categories = {
        "gambling",
        "crypto",
        "money transfer",
    }

    if merchant_category:

        category = (
            merchant_category.lower()
        )

        if category in high_risk_categories:

            risk_score += 25

            reasons.append(
                "Merchant category requires additional scrutiny."
            )

    # Rule 3: missing device information

    if not device_id:

        risk_score += 15

        reasons.append(
            "Device information is missing."
        )

    # Rule 4: missing location

    if not location:

        risk_score += 10

        reasons.append(
            "Transaction location is missing."
        )

    # Rule 5: transaction velocity

    if velocity_count >= 5:

        risk_score += 30

        reasons.append(
            "High transaction frequency detected within the recent time window."
        )

    # Rule 6: recent transaction amount

    if velocity_amount >= 50000:

        risk_score += 25

        reasons.append(
            "High cumulative transaction amount detected within the recent time window."
        )

    # Keep score between 0 and 100

    risk_score = min(
        risk_score,
        100,
    )

    if risk_score >= 60:

        risk_level = "HIGH"

    elif risk_score >= 30:

        risk_level = "MEDIUM"

    else:

        risk_level = "LOW"

    if not reasons:

        reasons.append(
            "No suspicious rule was triggered."
        )

    return FraudAssessment(
        risk_level=risk_level,
        risk_score=risk_score,
        reasons=reasons,
    )