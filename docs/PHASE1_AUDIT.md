# Phase 1 backend audit

Audit completed against `main` at `ec0dc3f`.

## Confirmed scope

- Service creation initializes a persisted `UNKNOWN` state.
- Check ingestion is idempotent on `(service_id, external_id)` and handles concurrent duplicate insertion by re-reading the stored check.
- State transitions use chronological check evidence and persist only when the state changes.
- PostgreSQL constraints enforce allowed state values, check idempotency, and a single active state interval.
- `/health` is process liveness; `/ready` verifies a database query.
- The only migration is Alembic `0001_phase1`.

## Baseline correction made during audit

The PostgreSQL integration tests used a module-level async engine across function-scoped pytest event loops. A pooled asyncpg connection could be finalized after its originating event loop closed, producing `RuntimeError: Event loop is closed` during `test_health_and_readiness_are_distinct` teardown.

`clean_database` now disposes the engine in its own teardown. This changes test resource lifecycle only; it does not remove assertions, alter production transition rules, or weaken the verifier.
