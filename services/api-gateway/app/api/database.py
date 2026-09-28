from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import engine


router = APIRouter(
    prefix="/api/v1/database",
    tags=["Database"],
)


@router.get("/health")
async def database_health():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_database()"))
            database_name = result.scalar()

        return {
            "service": "postgresql",
            "status": "healthy",
            "database": database_name,
        }

    except Exception as exc:
        return {
            "service": "postgresql",
            "status": "unhealthy",
            "error": str(exc),
        }