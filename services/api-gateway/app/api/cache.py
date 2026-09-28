from fastapi import APIRouter

from app.core.redis import get_redis


router = APIRouter(
    prefix="/api/v1/cache",
    tags=["Cache"],
)


@router.get("/health")
async def cache_health():
    try:
        redis_client = get_redis()

        response = redis_client.ping()

        return {
            "service": "redis",
            "status": "healthy",
            "ping": response,
        }

    except Exception as exc:
        return {
            "service": "redis",
            "status": "unhealthy",
            "error": str(exc),
        }