from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import SummaryResponse
from app.db.models import ExecutiveSummary
from app.db.session import get_session

router = APIRouter(tags=["summary"])


@router.get("/api/summary", response_model=SummaryResponse)
async def get_summary(
    run_id: int,
    audience: str,
    session: AsyncSession = Depends(get_session),
):
    if audience not in ("controller", "executive"):
        raise HTTPException(status_code=400, detail="audience must be 'controller' or 'executive'")

    result = await session.execute(
        select(ExecutiveSummary)
        .where(ExecutiveSummary.run_id == run_id, ExecutiveSummary.audience == audience)
    )
    summary = result.scalar_one_or_none()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found for this run and audience")
    return summary
