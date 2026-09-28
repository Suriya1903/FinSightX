from datetime import datetime, timezone

from redis import Redis


WINDOW_SECONDS = 300

VELOCITY_COUNT_THRESHOLD = 5

VELOCITY_AMOUNT_THRESHOLD = 50000


def record_transaction(
    redis_client: Redis,
    customer_id: str,
    transaction_id: str,
    amount: float,
) -> dict:

    now = datetime.now(
        timezone.utc
    )

    timestamp = now.timestamp()

    key = f"fraud:velocity:{customer_id}"

    redis_client.zadd(
        key,
        {
            f"{transaction_id}:{amount}": timestamp
        },
    )

    minimum_timestamp = (
        timestamp - WINDOW_SECONDS
    )

    redis_client.zremrangebyscore(
        key,
        0,
        minimum_timestamp,
    )

    entries = redis_client.zrange(
        key,
        0,
        -1,
    )

    transaction_count = len(entries)

    total_amount = 0.0

    for entry in entries:

        try:
            _, amount_string = entry.rsplit(
                ":",
                1,
            )

            total_amount += float(
                amount_string
            )

        except ValueError:
            continue

    suspicious_count = (
        transaction_count
        >= VELOCITY_COUNT_THRESHOLD
    )

    suspicious_amount = (
        total_amount
        >= VELOCITY_AMOUNT_THRESHOLD
    )

    return {
        "transaction_count": transaction_count,
        "total_amount": round(
            total_amount,
            2,
        ),
        "suspicious_count": suspicious_count,
        "suspicious_amount": suspicious_amount,
    }