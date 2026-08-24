# Phase 1 baseline verification

## Verified environment

- Location: GitHub Codespaces workspace `/workspaces/SentinelOps`
- Codespace: `sentinelops-tunnel-probe-wgvrgr9jwq4hx`
- Revision: `ec0dc3f` (`main`)
- Docker: `29.7.2`
- Docker Compose: `v2.40.3`

## Command and result

The unchanged command below was run inside the Codespace:

```bash
bash scripts/verify_codespaces.sh
```

It completed successfully and emitted `SENTINELOPS BASELINE VERIFY SUCCEEDED` for API, PostgreSQL, migrations, service registration, check ingestion, health evaluation, anti-flapping, state transitions, recovery, duplicate protection, health history, persistence, and tests.

The verifier builds the Compose stack, confirms PostgreSQL and readiness, requires Alembic `0001_phase1`, seeds the demo service, runs the payments scenario, exercises the service endpoints, runs `pytest -q` inside the API container, and removes the temporary stack only after success.
