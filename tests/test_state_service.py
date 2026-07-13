import asyncio

from bw_flight_tracker.config import Settings
from bw_flight_tracker.services.state import StateService


def test_manual_selection_is_scoped_to_session() -> None:
    settings = Settings(mock_scenario="multiple_competing")
    service = StateService(settings)

    default_state = asyncio.run(service.current_state("viewer-a"))
    service.select_manual("viewer-a", "a1b2c3")
    manual_state = asyncio.run(service.current_state("viewer-a"))
    other_state = asyncio.run(service.current_state("viewer-b"))

    assert default_state["selection_mode"] == "automatic"
    assert manual_state["selection_mode"] == "manual"
    assert manual_state["primary"]["icao_hex"] == "a1b2c3"  # type: ignore[index]
    assert other_state["selection_mode"] == "automatic"


def test_stale_provider_scenario_returns_waiting_state() -> None:
    settings = Settings(mock_scenario="stale_provider")
    service = StateService(settings)
    state = asyncio.run(service.current_state("viewer-a"))

    assert state["status"] == "waiting"
    assert state["primary"] is None
    assert state["provider"]["stale"] is True  # type: ignore[index]
