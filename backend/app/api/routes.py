import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import HealthState, MonitoredService, ServiceCheck, ServiceHealthState
from app.schemas import CheckCreate, CheckIngestResponse, CheckOut, HealthHistoryOut, HealthOut, ServiceCreate, ServiceOut
from app.services.monitoring import ingest_check

router = APIRouter(prefix="/api/v1")


async def _service_or_404(session: AsyncSession, identifier: str) -> MonitoredService:
    try:
        service = await session.get(MonitoredService, uuid.UUID(identifier))
    except ValueError:
        service = await session.scalar(select(MonitoredService).where(MonitoredService.slug == identifier))
    if service is None:
        raise HTTPException(status_code=404, detail="service not found")
    return service


@router.post("/services", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
async def create_service(payload: ServiceCreate, session: AsyncSession = Depends(get_session)):
    service = MonitoredService(**payload.model_dump(mode="json"))
    async with session.begin():
        session.add(service)
        await session.flush()
        session.add(ServiceHealthState(service_id=service.id, state=HealthState.UNKNOWN, started_at=datetime.now(timezone.utc), trigger_reason="service registered"))
    await session.refresh(service)
    return service


@router.get("/services", response_model=list[ServiceOut])
async def list_services(session: AsyncSession = Depends(get_session)):
    return (await session.scalars(select(MonitoredService).order_by(MonitoredService.name))).all()


@router.get("/services/{service_id_or_slug}", response_model=ServiceOut)
async def get_service(service_id_or_slug: str, session: AsyncSession = Depends(get_session)):
    return await _service_or_404(session, service_id_or_slug)


@router.post("/services/{service_id}/checks", response_model=CheckIngestResponse, status_code=status.HTTP_201_CREATED)
async def submit_check(service_id: uuid.UUID, payload: CheckCreate, session: AsyncSession = Depends(get_session)):
    try:
        check, state_value, duplicate = await ingest_check(session, service_id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail="service not found")
    except IntegrityError:  # Concurrent same-id submission is safely retried as idempotent.
        await session.rollback()
        existing = await session.scalar(select(ServiceCheck).where(ServiceCheck.service_id == service_id, ServiceCheck.external_id == payload.external_id))
        if existing is None:
            raise
        active = await session.scalar(select(ServiceHealthState).where(ServiceHealthState.service_id == service_id, ServiceHealthState.ended_at.is_(None)))
        return CheckIngestResponse(check=existing, state=HealthState(active.state), duplicate=True)
    return CheckIngestResponse(check=check, state=state_value, duplicate=duplicate)


@router.get("/services/{service_id}/checks", response_model=list[CheckOut])
async def list_checks(service_id: uuid.UUID, session: AsyncSession = Depends(get_session), limit: int = Query(default=100, ge=1, le=500)):
    await _service_or_404(session, str(service_id))
    return (await session.scalars(select(ServiceCheck).where(ServiceCheck.service_id == service_id).order_by(ServiceCheck.checked_at).limit(limit))).all()


@router.get("/services/{service_id}/health", response_model=HealthOut)
async def current_health(service_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    await _service_or_404(session, str(service_id))
    active = await session.scalar(select(ServiceHealthState).where(ServiceHealthState.service_id == service_id, ServiceHealthState.ended_at.is_(None)))
    return active


@router.get("/services/{service_id}/health-history", response_model=list[HealthHistoryOut])
async def health_history(service_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    await _service_or_404(session, str(service_id))
    return (await session.scalars(select(ServiceHealthState).where(ServiceHealthState.service_id == service_id).order_by(ServiceHealthState.started_at, ServiceHealthState.created_at))).all()

