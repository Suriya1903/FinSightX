from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User


class AuthenticationError(Exception):
    pass


class ConflictError(Exception):
    pass


def register_user(
    db: Session,
    username: str,
    email: str,
    password: str,
) -> User:

    existing_user = db.execute(
        select(User).where(
            or_(
                User.username == username,
                User.email == email,
            )
        )
    ).scalar_one_or_none()

    if existing_user is not None:

        if existing_user.username == username:
            raise ConflictError(
                "Username already exists."
            )

        raise ConflictError(
            "Email already exists."
        )

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role="USER",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    username: str,
    password: str,
) -> tuple[User, str]:

    user = db.execute(
        select(User).where(
            User.username == username
        )
    ).scalar_one_or_none()

    if user is None:
        raise AuthenticationError(
            "Invalid username or password."
        )

    if not user.is_active:
        raise AuthenticationError(
            "User account is inactive."
        )

    if not verify_password(
        password,
        user.password_hash,
    ):
        raise AuthenticationError(
            "Invalid username or password."
        )

    access_token = create_access_token(
        subject=str(user.id),
        role=user.role,
    )

    return user, access_token


def get_token_expiry_seconds() -> int:
    return settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
