import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.responses import StreamingResponse

from app.api.schemas import (
    WorkflowRunCreate,
    WorkflowRunDetailResponse,
    WorkflowRunResponse,
)
from app.api.sse import format_sse_event
from app.core.event_bus import create_queue, get_queue, remove_queue
from app.core.orchestrator import launch_workflow
from app.db.models import WorkflowRun
from app.db.session import get_session

router = APIRouter(tags=["workflows"])

VALID_WORKFLOW_TYPES = {"consolidation", "performance"}


@router.post("/api/workflows/run", response_model=WorkflowRunResponse)
async def create_workflow_run(
    body: WorkflowRunCreate,
    session: AsyncSession = Depends(get_session),
):
    if body.workflow_type not in VALID_WORKFLOW_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid workflow_type: {body.workflow_type}")

    run = WorkflowRun(workflow_type=body.workflow_type, status="pending")
    session.add(run)
    await session.commit()
    await session.refresh(run)

    queue = create_queue(run.id)
    launch_workflow(body.workflow_type, run.id, queue, body.language)

    return WorkflowRunResponse(run_id=run.id, status=run.status)


@router.get("/api/workflows/{run_id}/stream")
async def stream_workflow(run_id: int):
    """SSE endpoint that streams workflow events in real time."""
    queue = get_queue(run_id)
    if queue is None:
        raise HTTPException(status_code=404, detail="No active stream for this run")

    async def event_generator():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=20.0)
                    if event is None:
                        break
                    yield event
                except asyncio.TimeoutError:
                    yield format_sse_event("heartbeat", {})
        finally:
            remove_queue(run_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/api/workflows/latest", response_model=WorkflowRunDetailResponse | None)
async def get_latest_workflow(
    workflow_type: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(WorkflowRun)
        .where(WorkflowRun.workflow_type == workflow_type, WorkflowRun.status == "completed")
        .options(selectinload(WorkflowRun.steps))
        .order_by(WorkflowRun.completed_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()
    return run


@router.get("/api/workflows/{run_id}", response_model=WorkflowRunDetailResponse)
async def get_workflow_run(
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
    return run
