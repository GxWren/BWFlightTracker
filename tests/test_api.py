import pytest

fastapi_testclient = pytest.importorskip("fastapi.testclient")

from bw_flight_tracker.main import app  # noqa: E402

TestClient = fastapi_testclient.TestClient


def test_health_ready() -> None:
    response = TestClient(app).get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_public_state_omits_coordinates() -> None:
    response = TestClient(app).get("/api/v1/state")
    assert response.status_code == 200
    text = response.text.lower()
    assert "latitude" not in text
    assert "longitude" not in text
    assert "home_latitude" not in text
    assert response.json()["primary"] is not None
