# Phase 2 verification

Verified in GitHub Codespaces at `d7e83ca`, with Alembic revision `0002_phase2`.

`bash scripts/verify_phase2.sh` passed with **11 tests** and emitted `SENTINELOPS PHASE2 VERIFY SUCCEEDED`.

The Payments scenario reached `UNKNOWN -> HEALTHY -> DEGRADED -> DOWN -> RECOVERING -> HEALTHY`. The degraded rule opens a WARNING alert and resolves on DOWN; the down rule opens a CRITICAL alert and resolves on RECOVERING. The critical alert opens the sole incident; it remains open through recovery and resolves only at HEALTHY. The recovery-failure integration test verifies `DOWN -> RECOVERING -> DOWN -> RECOVERING -> HEALTHY` keeps one incident and records ordered lifecycle events.
