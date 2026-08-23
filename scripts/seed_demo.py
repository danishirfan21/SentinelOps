"""Idempotently register the Phase 1 demo services."""
import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from sqlalchemy import select

from app.db import SessionLocal
from app.models import HealthState, MonitoredService, ServiceHealthState

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


if __name__ == "__main__":
    asyncio.run(main())
