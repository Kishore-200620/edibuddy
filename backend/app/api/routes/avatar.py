from fastapi import APIRouter, HTTPException
from app.avatar.service import AvatarService

router = APIRouter(
    prefix="/avatar",
    tags=["Avatar"],
)

avatar_service = AvatarService()


@router.post("/session")
async def create_avatar_session():
    try:
        session_data = await avatar_service.create_session()
        return session_data
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create avatar session: {exc}",
        )