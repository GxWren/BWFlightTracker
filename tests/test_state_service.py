import asyncio

import httpx

from bw_flight_tracker.config import Settings
from bw_flight_tracker.domain.models import AircraftState, EnrichedFlight
from bw_flight_tracker.services.state import StateService


def test_manual_selection_is_scoped_to_session() -> None:
    settings = Settings(
        aircraft_provider="mock",
        mock_scenario="multiple_competing",
        home_latitude=41.88,
        home_longitude=-87.63,
        detection_radius_miles=10,
    )
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
    settings = Settings(
        aircraft_provider="mock",
        mock_scenario="stale_provider",
        home_latitude=41.88,
        home_longitude=-87.63,
        detection_radius_miles=10,
    )
    service = StateService(settings)
    state = asyncio.run(service.current_state("viewer-a"))

    assert state["status"] == "waiting"
    assert state["primary"] is None
    assert state["provider"]["stale"] is True  # type: ignore[index]


def test_provider_http_error_returns_waiting_state() -> None:
    class FailingProvider:
        async def fetch_aircraft(self) -> list[object]:
            raise httpx.ConnectError("certificate verify failed")

    settings = Settings(aircraft_provider="mock")
    service = StateService(settings)
    service.provider = FailingProvider()  # type: ignore[assignment]

    state = asyncio.run(service.current_state("viewer-a"))

    assert state["status"] == "waiting"
    assert state["primary"] is None
    assert state["provider"]["stale"] is True  # type: ignore[index]
    assert state["provider"]["error"] == "provider_unavailable"  # type: ignore[index]


def test_only_primary_aircraft_is_enriched() -> None:
    class CountingEnrichment:
        def __init__(self) -> None:
            self.requests: list[str] = []

        async def enrich(self, aircraft: AircraftState) -> EnrichedFlight:
            self.requests.append(aircraft.icao_hex)
            return EnrichedFlight(
                "test",
                aircraft.observed_at_utc,
                airline_name="Selected Air",
                flight_identifier=aircraft.callsign,
            )

    settings = Settings(
        aircraft_provider="mock",
        mock_scenario="multiple_competing",
        home_latitude=41.88,
        home_longitude=-87.63,
        detection_radius_miles=10,
    )
    service = StateService(settings)
    enrichment = CountingEnrichment()
    service.enrichment = enrichment  # type: ignore[assignment]

    state = asyncio.run(service.current_state("viewer-a"))

    assert len(enrichment.requests) == 1
    assert state["primary"]["airline_name"] == "Selected Air"  # type: ignore[index]
    assert all(
        aircraft["airline_name"] is None
        for aircraft in state["nearby"]  # type: ignore[union-attr]
        if aircraft["icao_hex"] != state["primary"]["icao_hex"]  # type: ignore[index]
    )


def test_resume_auto_resets_selector_to_current_closest() -> None:
    settings = Settings(
        aircraft_provider="mock",
        mock_scenario="multiple_competing",
        home_latitude=41.88,
        home_longitude=-87.63,
        detection_radius_miles=10,
    )
    service = StateService(settings)
    service.select_manual("viewer-a", "abc999")
    manual_state = asyncio.run(service.current_state("viewer-a"))

    service.resume_auto("viewer-a")
    automatic_state = asyncio.run(service.current_state("viewer-a"))

    assert manual_state["selection_mode"] == "manual"
    assert automatic_state["selection_mode"] == "automatic"
    assert automatic_state["primary"]["icao_hex"] == automatic_state["nearby"][0]["icao_hex"]  # type: ignore[index]
