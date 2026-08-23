#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
cleanup_success() { docker compose down -v --remove-orphans; }
trap 'echo "Verification failed. Containers were left running; inspect with: docker compose logs"' ERR

docker compose down -v --remove-orphans
docker compose build
docker compose up -d

for _ in {1..40}; do docker compose exec -T postgres pg_isready -U sentinelops -d sentinelops && break; sleep 2; done
for _ in {1..40}; do curl -fsS http://localhost:8000/ready >/dev/null && break; sleep 2; done
curl -fsS http://localhost:8000/ready >/dev/null
test "$(docker compose exec -T api alembic current | tail -1 | awk '{print $1}')" = "0001_phase1"

docker compose exec -T api python /app/scripts/seed_demo.py
python simulator/payments_scenario.py
PAYMENTS_ID="$(curl -fsS http://localhost:8000/api/v1/services/payments-api | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
curl -fsS "http://localhost:8000/api/v1/services/${PAYMENTS_ID}/checks" >/dev/null
curl -fsS "http://localhost:8000/api/v1/services/${PAYMENTS_ID}/health" >/dev/null
curl -fsS "http://localhost:8000/api/v1/services/${PAYMENTS_ID}/health-history" >/dev/null
docker compose exec -T api pytest -q

cleanup_success
trap - ERR
cat <<'MARKER'
SENTINELOPS BASELINE VERIFY SUCCEEDED:
API
PostgreSQL
migrations
service registration
check ingestion
health evaluation
anti-flapping
state transitions
recovery
duplicate protection
health history
persistence
tests
MARKER

