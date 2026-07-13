import os

from fastapi.testclient import TestClient

os.environ["AIRCRAFT_PROVIDER"] = "mock"
os.environ["HOME_LATITUDE"] = "41.88"
os.environ["HOME_LONGITUDE"] = "-87.63"
os.environ["DETECTION_RADIUS_MILES"] = "10"

from bw_flight_tracker.main import app


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
