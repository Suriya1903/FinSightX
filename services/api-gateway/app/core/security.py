from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

import os


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change_me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> str:
    """
    Extract the JWT access token from the Authorization header.
    """

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials


def decode_access_token(
    token: str = Depends(get_current_token),
) -> dict[str, Any]:
    """
    Decode and validate the JWT access token.
    """

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        subject = payload.get("sub")

        if not subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(
    payload: dict[str, Any] = Depends(decode_access_token),
) -> dict[str, Any]:
    """
    Return the authenticated user's identity and role.
    """

    return {
        "user_id": payload["sub"],
        "role": payload.get("role", "USER"),
    }


def require_roles(*allowed_roles: str):
    """
    Create a dependency that allows only specific roles.

    Example:

        Depends(require_roles("ADMIN"))

    This means only ADMIN users can access the endpoint.
    """

    normalized_roles = {
        role.upper()
        for role in allowed_roles
    }

    def role_checker(
        current_user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:

        user_role = str(
            current_user.get("role", "USER")
        ).upper()

        if user_role not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return current_user

    return role_checker


def require_admin(
    current_user: dict[str, Any] = Depends(
        require_roles("ADMIN")
    ),
) -> dict[str, Any]:
    """
    Convenience dependency for ADMIN-only endpoints.
    """

    return current_user


def require_user_or_admin(
    current_user: dict[str, Any] = Depends(
        require_roles("USER", "ADMIN")
    ),
) -> dict[str, Any]:
    """
    Allow both USER and ADMIN roles.
    """

    return current_user