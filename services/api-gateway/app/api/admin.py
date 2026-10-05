from fastapi import APIRouter, Depends

from app.core.security import require_admin


router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Administration"],
)


@router.get("/test")
async def admin_test(
    current_user: dict = Depends(require_admin),
):
    """
    Test endpoint used to verify ADMIN role-based authorization.
    """

    return {
        "message": "Admin access granted.",
        "user_id": current_user["user_id"],
        "role": current_user["role"],
        "authorization": "ADMIN",
    }