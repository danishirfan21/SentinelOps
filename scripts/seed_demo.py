"""Idempotently register the Phase 1 demo services."""
import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from sqlalchemy import select

from app.db import SessionLocal
from app.models import AlertConditionType, AlertRule, AlertSeverity, HealthState, MonitoredService, ServiceHealthState

SERVICES = [
    ("API Gateway", "api-gateway", "Public API entry point"),
    ("Payments API", "payments-api", "Payment processing service"),
    ("Search API", "search-api", "Search service"),
]


async def main() -> None:
    async with SessionLocal() as session, session.begin():
        for name, slug, description in SERVICES:
            if await session.scalar(select(MonitoredService).where(MonitoredService.slug == slug)):
                print(f"exists: {name}")
                continue
            service = MonitoredService(name=name, slug=slug, description=description)
            session.add(service)
            await session.flush()
            session.add(ServiceHealthState(service_id=service.id, state=HealthState.UNKNOWN, started_at=datetime.now(timezone.utc), trigger_reason="service registered"))
            print(f"created: {name}")
        payments = await session.scalar(select(MonitoredService).where(MonitoredService.slug == "payments-api"))
        for name, slug, condition, severity in [
            ("Payments degraded", "payments-degraded", AlertConditionType.STATE_DEGRADED, AlertSeverity.WARNING),
            ("Payments down", "payments-down", AlertConditionType.STATE_DOWN, AlertSeverity.CRITICAL),
        ]:
            if await session.scalar(select(AlertRule).where(AlertRule.service_id == payments.id, AlertRule.slug == slug)):
                print(f"exists rule: {name}")
            else:
                session.add(AlertRule(service_id=payments.id, name=name, slug=slug, condition_type=condition, severity=severity))
                print(f"created rule: {name}")


if __name__ == "__main__":
    asyncio.run(main())
