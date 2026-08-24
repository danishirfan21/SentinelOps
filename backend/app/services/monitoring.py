import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import HealthState, MonitoredService, ServiceCheck, ServiceHealthState
from app.schemas import CheckCreate
from app.services.health_engine import CheckEvidence, evaluate_state
from app.services.alert_engine import evaluate_alert_rules


async def ingest_check(session: AsyncSession, service_id: uuid.UUID, payload: CheckCreate) -> tuple[ServiceCheck, HealthState, bool]:
    """Atomically persist a check and any resulting state interval transition."""
    async with session.begin():
        service = await session.get(MonitoredService, service_id)
        if service is None:
            raise LookupError("service not found")

        existing = await session.scalar(select(ServiceCheck).where(ServiceCheck.service_id == service_id, ServiceCheck.external_id == payload.external_id))
        active = await session.scalar(
            select(ServiceHealthState)
            .where(ServiceHealthState.service_id == service_id, ServiceHealthState.ended_at.is_(None))
            .with_for_update()
        )
        if active is None:  # Defensive invariant; service creation always initializes UNKNOWN.
            raise RuntimeError("service has no active health state")
        if existing is not None:
            return existing, HealthState(active.state), True

        check = ServiceCheck(service_id=service_id, **payload.model_dump())
        session.add(check)
        await session.flush()

        checks = (await session.scalars(
            select(ServiceCheck).where(ServiceCheck.service_id == service_id).order_by(ServiceCheck.checked_at.asc(), ServiceCheck.created_at.asc())
        )).all()
        evidence = [CheckEvidence(success=item.success, latency_ms=item.latency_ms) for item in checks]
        next_state, reason = evaluate_state(HealthState(active.state), evidence)
        if next_state != HealthState(active.state):
            active.ended_at = check.checked_at
            transition = ServiceHealthState(
                service_id=service_id,
                state=next_state,
                started_at=check.checked_at,
                trigger_reason=reason,
                triggering_check_id=check.id,
            )
            session.add(transition)
            await session.flush()
            await evaluate_alert_rules(session, service_id, transition)
        return check, next_state, False

