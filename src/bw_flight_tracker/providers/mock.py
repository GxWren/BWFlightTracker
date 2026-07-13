from datetime import UTC, datetime

from bw_flight_tracker.domain.models import AircraftState, EnrichedFlight


class MockAircraftProvider:
    async def fetch_aircraft(self) -> list[AircraftState]:
        now = datetime.now(UTC)
        return [
            AircraftState(
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
            ),
            AircraftState(
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
            ),
            AircraftState(
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
            ),
        ]


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
        return EnrichedFlight(
            "mock",
            now,
            flight_identifier=aircraft.callsign,
            registration=aircraft.registration,
            confidence="unavailable",
        )
