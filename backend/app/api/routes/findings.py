from fastapi import APIRouter, Depends
from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import FindingResponse
from app.db.models import Finding
from app.db.session import get_session

router = APIRouter(tags=["findings"])

# Sort by severity: high=1, medium=2, low=3
SEVERITY_ORDER = case(
    (Finding.severity == "high", 1),
    (Finding.severity == "medium", 2),
    (Finding.severity == "low", 3),
    else_=4,
)


@router.get("/api/findings", response_model=list[FindingResponse])
async def get_findings(
    run_id: int,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Finding)
        .where(Finding.run_id == run_id)
        .order_by(SEVERITY_ORDER, Finding.id)
    )
    return result.scalars().all()
