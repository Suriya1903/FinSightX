import os

import redis


REDIS_HOST = os.getenv(
    "REDIS_HOST",
    "redis",
)

REDIS_PORT = int(
    os.getenv(
        "REDIS_PORT",
        "6379",
    )
)


redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
)


def get_redis() -> redis.Redis:
    return redis_client


def is_event_processed(
    event_id: str,
) -> bool:

    key = f"fraud:processed:{event_id}"

    return bool(
        redis_client.exists(key)
    )


def mark_event_processed(
    event_id: str,
) -> None:

    key = f"fraud:processed:{event_id}"

    redis_client.set(
        key,
        "1",
        ex=86400,
    )