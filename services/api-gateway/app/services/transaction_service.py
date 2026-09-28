import os

import httpx


TRANSACTION_SERVICE_URL = os.getenv(
    "TRANSACTION_SERVICE_URL",
    "http://transaction-service:8010",
)


async def list_transactions():
    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:

        response = await client.get(
            f"{TRANSACTION_SERVICE_URL}/api/v1/transactions"
        )

        response.raise_for_status()

        return response.json()


async def get_transaction(
    transaction_id: str,
):
    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:

        response = await client.get(
            f"{TRANSACTION_SERVICE_URL}/api/v1/transactions/{transaction_id}"
        )

        response.raise_for_status()

        return response.json()


async def create_transaction(
    transaction_data: dict,
):
    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:

        response = await client.post(
            f"{TRANSACTION_SERVICE_URL}/api/v1/transactions",
            json=transaction_data,
        )

        response.raise_for_status()

        return response.json()