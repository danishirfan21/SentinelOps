#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
trap 'echo "Phase 2 verification failed. Containers were left running; inspect with: docker compose logs"' ERR
docker compose down -v --remove-orphans
docker compose build
docker compose up -d
for _ in {1..40}; do curl -fsS http://localhost:8000/ready >/dev/null && break; sleep 2; done
curl -fsS http://localhost:8000/ready >/dev/null
test "$(docker compose exec -T api alembic current | tail -1 | awk '{print $1}')" = "0002_phase2"
docker compose exec -T api python /app/scripts/seed_demo.py
python simulator/payments_scenario.py
docker compose exec -T api pytest -q
docker compose down -v --remove-orphans
trap - ERR
cat <<'MARKER'
SENTINELOPS PHASE2 VERIFY SUCCEEDED:
API
PostgreSQL
migrations
alert rules
warning alerts
critical alerts
alert resolution
incident opening
incident events
recovery tracking
incident resolution
duplicate prevention
recovery failure handling
persistence
tests
MARKER
