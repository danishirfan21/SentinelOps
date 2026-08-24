# Phase 3 verification

Verified in the existing GitHub Codespace `sentinelops-tunnel-probe-wgvrgr9jwq4hx` on 2026-08-24.

The real command `bash scripts/verify_frontend.sh` passed and emitted `SENTINELOPS FRONTEND VERIFY SUCCEEDED`. It performed dependency installation, the TypeScript build, the frontend test suite, Compose image builds, PostgreSQL/API/frontend startup, demo seeding, the Payments scenario, frontend-facing API assertions, and the browser-origin CORS preflight assertion.

The same Codespace then passed the required backend verifiers:

- `bash scripts/verify_codespaces.sh` emitted `SENTINELOPS BASELINE VERIFY SUCCEEDED` with 12 tests passed.
- `bash scripts/verify_phase2.sh` emitted `SENTINELOPS PHASE2 VERIFY SUCCEEDED`.

Two verifier defects were corrected rather than bypassed: the frontend verifier now rebuilds the API image before asserting its CORS contract, and the baseline verifier now requires the actual committed Alembic head, `0002_phase2`, instead of the superseded Phase 1-only revision.
