from fastapi.testclient import TestClient

from app.main import app


def test_local_dashboard_origin_is_allowed_but_unlisted_origin_is_not() -> None:
    client = TestClient(app)
    allowed = client.options("/health", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
    denied = client.options("/health", headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "GET"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in denied.headers
