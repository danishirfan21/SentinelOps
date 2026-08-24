# SentinelOps architecture

SentinelOps is a PostgreSQL-backed service-health monitoring core. Its Phase 1 boundary is deliberately limited to service registration, check ingestion, deterministic state evaluation, and persisted health-state history.

## Runtime path

```text
health observation
  -> FastAPI /api/v1/services/{id}/checks
  -> transactional ingestion service
  -> PostgreSQL service_checks
  -> pure health-state evaluator
  -> active and historical service_health_states rows
```

- FastAPI exposes liveness at `/health`, database readiness at `/ready`, and the versioned service API.
- SQLAlchemy uses the async `asyncpg` PostgreSQL driver. Alembic revision `0001_phase1` owns the Phase 1 schema.
- `ingest_check` writes the check and any state transition in one transaction, locks the active state row, and returns an existing check for a repeated `(service_id, external_id)` submission.
- Each registered service starts with one `UNKNOWN` state interval. A PostgreSQL partial unique index ensures only one interval per service has `ended_at IS NULL`.
- `health_engine.evaluate_state` is pure and deterministic. It implements the anti-flapping rules for `UNKNOWN`, `HEALTHY`, `DEGRADED`, `DOWN`, and `RECOVERING`.

## Persistence model

`monitored_services` owns service metadata. `service_checks` stores observations ordered by `checked_at`; its `(service_id, external_id)` unique constraint is the idempotency boundary. `service_health_states` stores intervals, preserving state history and the check/reason that triggered a transition.

## Phase 2 alert and incident flow

```text
health transition -> rule evaluation -> alert lifecycle -> incident lifecycle -> incident events
```

Rules match exact persisted states (`STATE_DEGRADED` or `STATE_DOWN`), so alerts are rule-specific. Open alerts are unique per rule/service. A CRITICAL alert opens at most one service incident. Alert clearance at `RECOVERING` does not resolve its incident; `RECOVERY_STARTED` is persisted, and the incident resolves only after `HEALTHY`. Evaluation, alert updates, and incident events occur in the check-ingestion transaction.

## Phase 3 dashboard path

```text
React/Vite dashboard
  -> shared API client (VITE_API_BASE_URL)
  -> FastAPI /api/v1 endpoints
  -> transactional ingestion + alert/incident lifecycle
  -> PostgreSQL
```

The frontend has focused operational views for the service overview, service detail and health history, alerts, incidents, and incident detail. Its TypeScript API client is the sole browser-to-API boundary. The API permits the configured dashboard origins through FastAPI CORS middleware; Docker Compose provides the default local API origin and publishes the dashboard on port 5173.

## Deliberately excluded

SentinelOps does not implement a scheduler or active probe executor, authentication, notification delivery, acknowledgement/ownership workflows, escalation, silencing, maintenance windows, distributed workers, or production deployment automation.
