from datetime import UTC, datetime
from typing import Literal

from bw_flight_tracker.domain.models import AircraftState, EnrichedFlight

MockScenarioName = Literal[
    "no_flights",
    "one_commercial",
    "multiple_competing",
    "missing_route",
    "private_aircraft",
    "stale_provider",
    "provider_recovery",
]


class MockAircraftProvider:
    """Deterministic Phase 1 provider with named scenarios for UI and tests."""

    def __init__(self, scenario: str = "multiple_competing") -> None:
        self.scenario = scenario
        self._poll_count = 0

    async def fetch_aircraft(self) -> list[AircraftState]:
        self._poll_count += 1
        scenario = self.scenario
        if scenario == "provider_recovery" and self._poll_count <= 1:
            scenario = "stale_provider"
        return _scenario_aircraft(scenario, datetime.now(UTC))


class MockEnrichmentProvider:
    async def enrich(self, aircraft: AircraftState) -> EnrichedFlight | None:
        now = datetime.now(UTC)
        if aircraft.callsign == "UAL123":
            return EnrichedFlight(
                "mock",
                now,
                "United Airlines",
                "UA123",
                "ORD",
                "DEN",
                "Chicago",
                "Denver",
                "Boeing",
                "737-800",
                aircraft.registration,
                "confirmed",
            )
        if aircraft.callsign == "DAL456":
            return EnrichedFlight(
                "mock",
                now,
                "Delta Air Lines",
                "DL456",
                "MSP",
                "ATL",
                "Minneapolis",
                "Atlanta",
                "Airbus",
                "A321",
                aircraft.registration,
                "confirmed",
            )
        if aircraft.callsign == "SWA789":
            return EnrichedFlight(
                "mock",
                now,
                "Southwest Airlines",
                "WN789",
                "MDW",
                "STL",
                "Chicago",
                "St. Louis",
                "Boeing",
                "737 MAX 8",
                aircraft.registration,
                "confirmed",
            )
        return EnrichedFlight(
            "mock",
            now,
            flight_identifier=aircraft.callsign,
            registration=aircraft.registration,
            confidence="unavailable",
        )


def _scenario_aircraft(scenario: str, now: datetime) -> list[AircraftState]:
    scenarios = {
        "no_flights": [],
        "one_commercial": [_ual(now)],
        "multiple_competing": [_ual(now), _private(now), _delta(now)],
        "missing_route": [_unknown_commercial(now)],
        "private_aircraft": [_private(now)],
        "stale_provider": [_stale(now)],
    }
    return scenarios.get(scenario, scenarios["multiple_competing"])


def _ual(now: datetime) -> AircraftState:
    return AircraftState(
        "a1b2c3",
        41.935,
        -87.69,
        now,
        "UAL123",
        "N123UA",
        "B738",
        "Boeing 737-800",
        6200,
        210,
        150,
        -300,
        position_age_seconds=2,
        source_type="adsb_icao",
    )


def _delta(now: datetime) -> AircraftState:
    return AircraftState(
        "abc999",
        42.01,
        -87.75,
        now,
        "DAL456",
        "N456DL",
        "A321",
        "Airbus A321",
        12000,
        260,
        170,
        -700,
        position_age_seconds=7,
        source_type="adsb_icao",
    )


def _private(now: datetime) -> AircraftState:
    return AircraftState(
        "d4e5f6",
        41.82,
        -87.55,
        now,
        "N987BW",
        "N987BW",
        "C172",
        "Cessna 172",
        2800,
        95,
        330,
        100,
        position_age_seconds=4,
        source_type="adsb_icao",
    )


def _unknown_commercial(now: datetime) -> AircraftState:
    return AircraftState(
        "baddad",
        41.91,
        -87.67,
        now,
        "SWA789",
        "N789SW",
        "B38M",
        "Boeing 737 MAX 8",
        5400,
        180,
        135,
        -200,
        position_age_seconds=3,
        source_type="adsb_icao",
    )


def _stale(now: datetime) -> AircraftState:
    return AircraftState(
        "faded1",
        41.9,
        -87.66,
        now,
        "UAL404",
        "N404UA",
        "B739",
        "Boeing 737-900",
        8000,
        220,
        90,
        0,
        position_age_seconds=90,
        source_type="adsb_icao",
    )
