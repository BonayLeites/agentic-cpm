from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.app_version}
