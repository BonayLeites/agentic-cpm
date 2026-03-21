from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas import AuditResponse
from app.db.models import WorkflowRun
from app.db.session import get_session

router = APIRouter(tags=["audit"])


@router.get("/api/audit", response_model=AuditResponse)
async def get_audit(
    run_id: int,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(WorkflowRun)
        .where(WorkflowRun.id == run_id)
        .options(selectinload(WorkflowRun.steps))
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found")

    return AuditResponse(
        run_id=run.id,
        workflow_type=run.workflow_type,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        total_duration_ms=run.total_duration_ms,
        total_findings=run.total_findings,
        total_cost=run.total_cost,
        overall_confidence=run.overall_confidence,
        steps=run.steps,
    )
