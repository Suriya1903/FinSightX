import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://finsightx:change_me@localhost:5434/finsightx",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


def get_db() -> Session:
    return Session(engine)