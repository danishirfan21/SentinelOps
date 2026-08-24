"""Deterministic incident lifecycle operations for persisted health transitions."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, AlertSeverity, HealthState, Incident, IncidentEvent, IncidentEventType, IncidentStatus, ServiceHealthState


async def _open_incident(session: AsyncSession, alert: Alert, transition: ServiceHealthState) -> tuple[Incident, bool]:
    incident = await session.scalar(
        select(Incident).where(Incident.service_id == alert.service_id, Incident.status == IncidentStatus.OPEN).with_for_update()
    )
    if incident is not None:
        return incident, False
    incident = Incident(
        service_id=alert.service_id,
        title="Critical service outage",
        severity=alert.severity,
        status=IncidentStatus.OPEN,
        opened_at=transition.started_at,
        opened_by_alert_id=alert.id,
    )
    session.add(incident)
    await session.flush()
    session.add(IncidentEvent(
        incident_id=incident.id, event_type=IncidentEventType.OPENED, occurred_at=transition.started_at,
        health_state_id=transition.id, alert_id=alert.id, message="Opened by critical alert",
    ))
    return incident, True


async def reconcile_incident(
    session: AsyncSession,
    service_id: uuid.UUID,
    transition: ServiceHealthState,
    newly_opened_critical_alerts: list[Alert],
) -> None:
    """Apply incident semantics after alerts have been updated for one transition."""
    incident: Incident | None = None
    opened = False
    for alert in newly_opened_critical_alerts:
        incident, created = await _open_incident(session, alert, transition)
        opened = opened or created

    if incident is None:
        incident = await session.scalar(
            select(Incident).where(Incident.service_id == service_id, Incident.status == IncidentStatus.OPEN).with_for_update()
        )
    if incident is None:
        return

    active_severity = await session.scalar(
        select(Alert.severity).where(Alert.service_id == service_id, Alert.state == "OPEN").order_by(Alert.severity.desc()).limit(1)
    )
    if active_severity is not None:
        incident.severity = active_severity

    state = HealthState(transition.state)
    if state == HealthState.RECOVERING:
        session.add(IncidentEvent(
            incident_id=incident.id, event_type=IncidentEventType.RECOVERY_STARTED, occurred_at=transition.started_at,
            health_state_id=transition.id, message="Recovery started; incident remains open until healthy",
        ))
    elif state == HealthState.HEALTHY:
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = transition.started_at
        session.add(IncidentEvent(
            incident_id=incident.id, event_type=IncidentEventType.RESOLVED, occurred_at=transition.started_at,
            health_state_id=transition.id, message="Resolved after healthy recovery",
        ))
    elif state == HealthState.DOWN and not opened:
        session.add(IncidentEvent(
            incident_id=incident.id, event_type=IncidentEventType.STATE_CHANGED, occurred_at=transition.started_at,
            health_state_id=transition.id, message="Service returned to down while incident remained open",
        ))
