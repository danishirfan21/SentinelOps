"""Submit the deterministic Payments API recovery scenario through the public API."""
import json
import os
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

API_URL = os.getenv("SENTINELOPS_API_URL", "http://localhost:8000").rstrip("/")


def request(method: str, path: str, body: dict | None = None):
    data = json.dumps(body).encode() if body else None
    req = Request(f"{API_URL}{path}", data=data, method=method, headers={"Content-Type": "application/json"})
    with urlopen(req) as response:
        return json.loads(response.read())


def main() -> None:
    service = request("GET", "/api/v1/services/payments-api")
    service_id = service["id"]
    initial = request("GET", f"/api/v1/services/{service_id}/health")["state"]
    transitions = [initial]
    start = datetime(2026, 8, 24, 10, 0, tzinfo=timezone.utc)
    steps = [(True, 145)] * 3 + [(True, 700)] * 2 + [(False, 1200)] * 3 + [(True, 180)] + [(True, 160)] * 3
    for index, (success, latency) in enumerate(steps, 1):
        payload = {"external_id": f"payments-scenario-{index:02d}", "checked_at": (start + timedelta(minutes=index)).isoformat().replace("+00:00", "Z"), "success": success, "status_code": 200 if success else 503, "latency_ms": latency}
        if not success:
            payload.update(error_type="HTTP_ERROR", error_message="Service unavailable")
        result = request("POST", f"/api/v1/services/{service_id}/checks", payload)
        state = result["state"]
        if state != transitions[-1]:
            transitions.append(state)
    print("Payments API:")
    for before, after in zip(transitions, transitions[1:]):
        print(f"{before} -> {after}")
    expected = ["UNKNOWN", "HEALTHY", "DEGRADED", "DOWN", "RECOVERING", "HEALTHY"]
    if transitions != expected:
        raise SystemExit(f"unexpected persisted transition sequence: {transitions}")


if __name__ == "__main__":
    main()

