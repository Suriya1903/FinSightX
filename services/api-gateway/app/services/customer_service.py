import os

import httpx


CUSTOMER_SERVICE_URL = os.getenv(
    "CUSTOMER_SERVICE_URL",
    "http://customer-service:8009",
)


async def list_customers():
    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:

        response = await client.get(
            f"{CUSTOMER_SERVICE_URL}/api/v1/customers"
        )

        response.raise_for_status()

        return response.json()


async def get_customer(
    customer_id: str,
):
    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:

        response = await client.get(
            f"{CUSTOMER_SERVICE_URL}/api/v1/customers/{customer_id}"
        )

        response.raise_for_status()

        return response.json()


async def create_customer(
    customer_data: dict,
):
    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:

        response = await client.post(
            f"{CUSTOMER_SERVICE_URL}/api/v1/customers",
            json=customer_data,
        )

        response.raise_for_status()

        return response.json()