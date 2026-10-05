import os


class Settings:
    APP_NAME: str = os.getenv(
        "APP_NAME",
        "FinSightX Auth Service",
    )

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://finsightx:change_me@localhost:5434/finsightx",
    )

    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "change_me",
    )

    JWT_ALGORITHM: str = os.getenv(
        "JWT_ALGORITHM",
        "HS256",
    )

    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv(
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
            "30",
        )
    )


settings = Settings()
