from __future__ import annotations

import os

import httpx


AUTH_SERVICE_URL = os.getenv(
    "AUTH_SERVICE_URL",
    "http://localhost:8001",
)


async def register_user(
    user_data: dict,
):
    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:

        response = await client.post(
            f"{AUTH_SERVICE_URL}/api/v1/auth/register",
            json=user_data,
        )

        return response


async def login_user(
    login_data: dict,
):
    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:

        response = await client.post(
            f"{AUTH_SERVICE_URL}/api/v1/auth/login",
            json=login_data,
        )

        return response


async def get_authenticated_user(
    token: str,
):
    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:

        response = await client.get(
            f"{AUTH_SERVICE_URL}/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        return response