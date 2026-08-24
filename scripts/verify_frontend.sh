#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
trap 'echo "Frontend verification failed. Containers were left running; inspect with: docker compose ps && docker compose logs"' ERR

pushd frontend >/dev/null
npm ci
npm test
npm run build
popd >/dev/null

docker compose down -v --remove-orphans
docker compose build frontend
docker compose up -d
for _ in {1..40}; do docker compose exec -T postgres pg_isready -U sentinelops -d sentinelops && break; sleep 2; done
for _ in {1..40}; do curl -fsS http://localhost:8000/ready >/dev/null && break; sleep 2; done
for _ in {1..40}; do curl -fsS http://localhost:5173 >/dev/null && break; sleep 2; done
curl -fsS http://localhost:8000/ready >/dev/null
curl -fsS http://localhost:5173 >/dev/null
docker compose exec -T api python /app/scripts/seed_demo.py
python simulator/payments_scenario.py
curl -fsS http://localhost:8000/api/v1/services | python -c 'import json,sys; assert json.load(sys.stdin)'
curl -fsS http://localhost:8000/api/v1/alerts | python -c 'import json,sys; assert json.load(sys.stdin)'
curl -fsS http://localhost:8000/api/v1/incidents | python -c 'import json,sys; assert json.load(sys.stdin)'
test "$(curl -fsS -X OPTIONS -D - -o /dev/null -H 'Origin: http://localhost:5173' -H 'Access-Control-Request-Method: GET' http://localhost:8000/api/v1/services | tr -d '\r' | grep -i '^access-control-allow-origin:' | awk '{print $2}')" = "http://localhost:5173"
docker compose down -v --remove-orphans
trap - ERR
cat <<'MARKER'
SENTINELOPS FRONTEND VERIFY SUCCEEDED:
dependencies
typescript
build
tests
docker
dashboard
api integration
MARKER
