from datetime import UTC, datetime

from bw_flight_tracker.domain.models import AircraftState, EnrichedFlight


class MockAircraftProvider:
    def __init__(self, scenario: str = "multiple_competing") -> None:
        self.scenario = scenario
        self.fetch_count = 0

    async def fetch_aircraft(self) -> list[AircraftState]:
        self.fetch_count += 1
        now = datetime.now(UTC)
        if self.scenario == "no_flights":
            return []
        if self.scenario == "one_commercial":
            return [self._ual(now)]
        if self.scenario == "missing_route":
            return [
                AircraftState(
                    "fed123",
                    41.91,
                    -87.66,
                    now,
                    "FDX321",
                    "N321FX",
                    "B763",
                    "Boeing 767-300F",
                    9000,
                    230,
                    150,
                    -500,
                    position_age_seconds=3,
                    source_type="adsb_icao",
                )
            ]
        if self.scenario == "private_aircraft":
            return [self._private(now)]
        if self.scenario == "stale_provider":
            return [self._ual(now, position_age_seconds=45)]
        if self.scenario == "provider_recovery" and self.fetch_count == 1:
            return [self._ual(now, position_age_seconds=45)]
        return [self._ual(now), self._private(now), self._delta(now)]

    def _ual(self, now: datetime, position_age_seconds: float = 2) -> AircraftState:
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
            position_age_seconds=position_age_seconds,
            source_type="adsb_icao",
        )

    def _private(self, now: datetime) -> AircraftState:
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

    def _delta(self, now: datetime) -> AircraftState:
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
        if aircraft.callsign == "FDX321":
            return EnrichedFlight(
                "mock",
                now,
                "FedEx",
                "FX321",
                manufacturer="Boeing",
                model="767-300F",
                registration=aircraft.registration,
                confidence="partial",
            )
        return EnrichedFlight(
            "mock",
            now,
            flight_identifier=aircraft.callsign,
            registration=aircraft.registration,
            confidence="unavailable",
        )
