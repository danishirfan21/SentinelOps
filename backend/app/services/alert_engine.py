"""Rule-specific alert evaluation triggered by persisted health-state transitions."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, AlertConditionType, AlertRule, AlertSeverity, AlertState, HealthState, ServiceHealthState
from app.services.incidents import reconcile_incident


def _matches(rule: AlertRule, state: HealthState) -> bool:
    return (
        rule.condition_type == AlertConditionType.STATE_DEGRADED and state == HealthState.DEGRADED
    ) or (
        rule.condition_type == AlertConditionType.STATE_DOWN and state == HealthState.DOWN
    )


async def evaluate_alert_rules(session: AsyncSession, service_id: uuid.UUID, transition: ServiceHealthState) -> None:
    """Open or resolve alerts, then reconcile the service incident in the same transaction."""
    rules = (await session.scalars(
        select(AlertRule).where(AlertRule.service_id == service_id, AlertRule.is_enabled.is_(True)).with_for_update()
    )).all()
    newly_opened_critical: list[Alert] = []
    state = HealthState(transition.state)
    for rule in rules:
        open_alert = await session.scalar(
            select(Alert).where(Alert.rule_id == rule.id, Alert.service_id == service_id, Alert.state == AlertState.OPEN).with_for_update()
        )
        if _matches(rule, state):
            if open_alert is None:
                alert = Alert(
                    rule_id=rule.id, service_id=service_id, state=AlertState.OPEN, severity=rule.severity,
                    opened_at=transition.started_at, triggering_health_state_id=transition.id,
                )
                session.add(alert)
                await session.flush()
                if rule.severity == AlertSeverity.CRITICAL:
                    newly_opened_critical.append(alert)
        elif open_alert is not None:
            open_alert.state = AlertState.RESOLVED
            open_alert.resolved_at = transition.started_at
            open_alert.resolution_health_state_id = transition.id

    await reconcile_incident(session, service_id, transition, newly_opened_critical)
