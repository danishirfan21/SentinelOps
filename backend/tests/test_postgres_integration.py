"""These tests require PostgreSQL and an Alembic-migrated DATABASE_URL; SQLite is never used."""
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import text

from app.db import engine
from app.main import app


@pytest.fixture(autouse=True)
async def clean_database():
    try:
        async with engine.begin() as connection:
            await connection.execute(text("TRUNCATE incident_events, incidents, alerts, alert_rules, service_health_states, service_checks, monitored_services CASCADE"))
        yield
    finally:
        # Tests use function-scoped event loops. Dispose pooled asyncpg
        # connections before that loop closes so they cannot be reused or
        # finalized by a subsequent test's loop.
        await engine.dispose()


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as result:
        yield result


async def create_payments(client):
    response = await client.post("/api/v1/services", json={"name": "Payments API", "slug": "payments-api"})
    assert response.status_code == 201
    return response.json()["id"]


async def send_check(client, service_id, number, success, latency):
    timestamp = datetime(2026, 8, 24, 10, 0, tzinfo=timezone.utc) + timedelta(minutes=number)
    body = {"external_id": f"test-{number}", "checked_at": timestamp.isoformat(), "success": success, "status_code": 200 if success else 503, "latency_ms": latency}
    if not success:
        body.update(error_type="HTTP_ERROR", error_message="unavailable")
    response = await client.post(f"/api/v1/services/{service_id}/checks", json=body)
    assert response.status_code == 201
    return body, response.json()


async def test_flagship_recovery_history_and_duplicate_protection(client):
    service_id = await create_payments(client)
    assert (await client.get(f"/api/v1/services/{service_id}/health")).json()["state"] == "UNKNOWN"

    number = 0
    for success, latency, count in [(True, 145, 3), (True, 700, 2), (False, 1200, 3), (True, 180, 1), (True, 160, 3)]:
        for _ in range(count):
            number += 1
            last_body, _ = await send_check(client, service_id, number, success, latency)

    current = await client.get(f"/api/v1/services/{service_id}/health")
    assert current.json()["state"] == "HEALTHY"
    history = await client.get(f"/api/v1/services/{service_id}/health-history")
    assert [item["state"] for item in history.json()] == ["UNKNOWN", "HEALTHY", "DEGRADED", "DOWN", "RECOVERING", "HEALTHY"]

    duplicate = await client.post(f"/api/v1/services/{service_id}/checks", json=last_body)
    assert duplicate.status_code == 201 and duplicate.json()["duplicate"] is True
    checks = await client.get(f"/api/v1/services/{service_id}/checks")
    assert len(checks.json()) == 12
    assert len((await client.get(f"/api/v1/services/{service_id}/health-history")).json()) == 6


async def test_health_and_readiness_are_distinct(client):
    assert (await client.get("/health")).json() == {"status": "ok"}
    assert (await client.get("/ready")).json() == {"status": "ready"}


async def test_checks_are_returned_in_checked_at_order_and_invalid_input_is_not_persisted(client):
    service_id = await create_payments(client)
    newer = await send_check(client, service_id, 2, True, 100)
    older = await send_check(client, service_id, 1, True, 100)
    listed = await client.get(f"/api/v1/services/{service_id}/checks")
    assert [item["external_id"] for item in listed.json()] == [older[0]["external_id"], newer[0]["external_id"]]
    invalid = await client.post(f"/api/v1/services/{service_id}/checks", json={"external_id": "bad", "checked_at": "2026-08-24T11:00:00Z", "success": True, "latency_ms": -1})
    assert invalid.status_code == 422
    assert len((await client.get(f"/api/v1/services/{service_id}/checks")).json()) == 2


async def test_alert_and_incident_recovery_lifecycle(client):
    service_id = await create_payments(client)
    for body in [
        {"name": "degraded", "slug": "degraded", "condition_type": "STATE_DEGRADED", "severity": "WARNING"},
        {"name": "down", "slug": "down", "condition_type": "STATE_DOWN", "severity": "CRITICAL"},
    ]:
        assert (await client.post(f"/api/v1/services/{service_id}/alert-rules", json=body)).status_code == 201
    number = 0
    for success, latency, count in [(True, 700, 3), (False, 1200, 3), (True, 100, 1)]:
        for _ in range(count):
            number += 1
            await send_check(client, service_id, number, success, latency)
    alerts = (await client.get("/api/v1/alerts", params={"service_id": str(service_id)})).json()
    assert [(alert["severity"], alert["state"]) for alert in alerts] == [("WARNING", "RESOLVED"), ("CRITICAL", "RESOLVED")]
    incident = (await client.get("/api/v1/incidents", params={"service_id": str(service_id)})).json()[0]
    assert incident["status"] == "OPEN"
    for _ in range(3):
        number += 1
        await send_check(client, service_id, number, True, 100)
    incident = (await client.get(f"/api/v1/incidents/{incident['id']}")).json()
    assert incident["status"] == "RESOLVED"
    events = (await client.get(f"/api/v1/incidents/{incident['id']}/events")).json()
    assert [event["event_type"] for event in events] == ["OPENED", "RECOVERY_STARTED", "RESOLVED"]


async def test_failed_recovery_keeps_one_incident(client):
    service_id = await create_payments(client)
    assert (await client.post(f"/api/v1/services/{service_id}/alert-rules", json={"name": "down", "slug": "down", "condition_type": "STATE_DOWN", "severity": "CRITICAL"})).status_code == 201
    number = 0
    for success in [False, False, False, True, False, True, True, True]:
        number += 1
        await send_check(client, service_id, number, success, 100)
    incidents = (await client.get("/api/v1/incidents", params={"service_id": str(service_id)})).json()
    assert len(incidents) == 1 and incidents[0]["status"] == "RESOLVED"
    events = (await client.get(f"/api/v1/incidents/{incidents[0]['id']}/events")).json()
    assert [event["event_type"] for event in events] == ["OPENED", "RECOVERY_STARTED", "STATE_CHANGED", "RECOVERY_STARTED", "RESOLVED"]
