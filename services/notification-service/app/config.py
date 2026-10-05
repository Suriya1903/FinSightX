from __future__ import annotations

import os


class Settings:
    APP_NAME: str = os.getenv(
        "APP_NAME",
        "FinSightX Notification Service",
    )

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://finsightx:change_me@localhost:5434/finsightx",
    )

    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "localhost:29092",
    )

    KAFKA_TOPIC: str = os.getenv(
        "KAFKA_TOPIC",
        "fraud.assessed",
    )

    KAFKA_GROUP_ID: str = os.getenv(
        "KAFKA_GROUP_ID",
        "finsightx-notification-service",
    )

    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "change_me",
    )

    JWT_ALGORITHM: str = os.getenv(
        "JWT_ALGORITHM",
        "HS256",
    )


settings = Settings()