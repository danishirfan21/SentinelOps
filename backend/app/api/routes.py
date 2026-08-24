import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Alert, AlertRule, AlertSeverity, AlertState, HealthState, Incident, IncidentEvent, IncidentStatus, MonitoredService, ServiceCheck, ServiceHealthState
from app.schemas import AlertOut, AlertRuleCreate, AlertRuleOut, AlertRulePatch, CheckCreate, CheckIngestResponse, CheckOut, HealthHistoryOut, HealthOut, IncidentEventOut, IncidentOut, ServiceCreate, ServiceOut
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


@router.post("/services/{service_id}/alert-rules", response_model=AlertRuleOut, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(service_id: uuid.UUID, payload: AlertRuleCreate, session: AsyncSession = Depends(get_session)):
    await _service_or_404(session, str(service_id))
    rule = AlertRule(service_id=service_id, **payload.model_dump())
    try:
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="alert rule slug already exists for service")
    return rule


@router.get("/services/{service_id}/alert-rules", response_model=list[AlertRuleOut])
async def list_alert_rules(service_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    await _service_or_404(session, str(service_id))
    return (await session.scalars(select(AlertRule).where(AlertRule.service_id == service_id).order_by(AlertRule.name))).all()


@router.get("/alert-rules/{rule_id}", response_model=AlertRuleOut)
async def get_alert_rule(rule_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    rule = await session.get(AlertRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="alert rule not found")
    return rule


@router.patch("/alert-rules/{rule_id}", response_model=AlertRuleOut)
async def patch_alert_rule(rule_id: uuid.UUID, payload: AlertRulePatch, session: AsyncSession = Depends(get_session)):
    rule = await session.get(AlertRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="alert rule not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(rule, field, value)
    await session.commit()
    await session.refresh(rule)
    return rule


@router.get("/alerts", response_model=list[AlertOut])
async def list_alerts(service_id: uuid.UUID | None = None, state: AlertState | None = None, severity: AlertSeverity | None = None, session: AsyncSession = Depends(get_session)):
    query = select(Alert)
    if service_id is not None:
        query = query.where(Alert.service_id == service_id)
    if state is not None:
        query = query.where(Alert.state == state)
    if severity is not None:
        query = query.where(Alert.severity == severity)
    return (await session.scalars(query.order_by(Alert.opened_at, Alert.created_at))).all()


@router.get("/alerts/{alert_id}", response_model=AlertOut)
async def get_alert(alert_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    alert = await session.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alert not found")
    return alert


@router.get("/incidents", response_model=list[IncidentOut])
async def list_incidents(service_id: uuid.UUID | None = None, status_filter: IncidentStatus | None = Query(default=None, alias="status"), severity: AlertSeverity | None = None, session: AsyncSession = Depends(get_session)):
    query = select(Incident)
    if service_id is not None:
        query = query.where(Incident.service_id == service_id)
    if status_filter is not None:
        query = query.where(Incident.status == status_filter)
    if severity is not None:
        query = query.where(Incident.severity == severity)
    return (await session.scalars(query.order_by(Incident.opened_at, Incident.created_at))).all()


@router.get("/incidents/{incident_id}", response_model=IncidentOut)
async def get_incident(incident_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    incident = await session.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="incident not found")
    return incident


@router.get("/incidents/{incident_id}/events", response_model=list[IncidentEventOut])
async def incident_events(incident_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    if await session.get(Incident, incident_id) is None:
        raise HTTPException(status_code=404, detail="incident not found")
    return (await session.scalars(select(IncidentEvent).where(IncidentEvent.incident_id == incident_id).order_by(IncidentEvent.occurred_at, IncidentEvent.created_at))).all()

