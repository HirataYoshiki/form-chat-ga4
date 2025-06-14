from fastapi import APIRouter, Depends
from backend.auth import AuthenticatedUser, get_current_active_user

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
    dependencies=[Depends(get_current_active_user)] # Apply auth to all routes in this router
)

@router.get("/me", response_model=AuthenticatedUser)
async def read_users_me(current_user: AuthenticatedUser = Depends(get_current_active_user)):
    """Get current authenticated user's profile information."""
    return current_user
