from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.db.session import async_session

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health():
    db_status = "connected"
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"
    return {"status": "ok", "db": db_status, "version": settings.app_version}
