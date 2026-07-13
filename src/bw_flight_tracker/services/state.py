from datetime import UTC, datetime

from bw_flight_tracker.config import Settings
from bw_flight_tracker.domain.selection import compute_candidate, eligible_candidates
from bw_flight_tracker.providers.mock import MockAircraftProvider, MockEnrichmentProvider


class StateService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider = MockAircraftProvider()
        self.enrichment = MockEnrichmentProvider()
        self.manual_icao: str | None = None
        self.last_update: datetime | None = None

    async def current_state(self) -> dict[str, object]:
        aircraft = await self.provider.fetch_aircraft()
        candidates = [
            compute_candidate(a, self.settings.home_latitude, self.settings.home_longitude)
            for a in aircraft
        ]
        eligible = eligible_candidates(candidates, self.settings.detection_radius_miles)
        enriched = {c.aircraft.icao_hex: await self.enrichment.enrich(c.aircraft) for c in eligible}
        primary = next((c for c in eligible if c.aircraft.icao_hex == self.manual_icao), None) or (
            eligible[0] if eligible else None
        )
        self.last_update = datetime.now(UTC)
        return {
            "status": "ok",
            "updated_at_utc": self.last_update.isoformat(),
            "provider": {"name": self.settings.aircraft_provider, "stale": False},
            "selection_mode": "manual" if self.manual_icao else "automatic",
            "primary": self._serialize(
                primary, enriched.get(primary.aircraft.icao_hex) if primary else None
            )
            if primary
            else None,
            "nearby": [self._serialize(c, enriched.get(c.aircraft.icao_hex)) for c in eligible],
        }

    def select_manual(self, icao_hex: str) -> None:
        self.manual_icao = icao_hex.lower()

    def resume_auto(self) -> None:
        self.manual_icao = None

    def _serialize(self, candidate, enrichment) -> dict[str, object]:  # type: ignore[no-untyped-def]
        aircraft = candidate.aircraft
        computed = candidate.computed
        speed_mph = (
            round(aircraft.ground_speed_knots * 1.150779) if aircraft.ground_speed_knots else None
        )
        return {
            "icao_hex": aircraft.icao_hex,
            "callsign": aircraft.callsign,
            "airline_name": enrichment.airline_name if enrichment else None,
            "flight_identifier": (enrichment.flight_identifier if enrichment else None)
            or aircraft.callsign,
            "origin_code": enrichment.origin_iata if enrichment else None,
            "destination_code": enrichment.destination_iata if enrichment else None,
            "origin_city": enrichment.origin_city if enrichment else None,
            "destination_city": enrichment.destination_city if enrichment else None,
            "aircraft_model": " ".join(
                x
                for x in [
                    enrichment.manufacturer if enrichment else None,
                    enrichment.model if enrichment else None,
                ]
                if x
            )
            or aircraft.aircraft_description,
            "registration": aircraft.registration,
            "altitude_ft": aircraft.altitude_ft,
            "ground_speed_mph": speed_mph,
            "distance_miles": round(computed.horizontal_distance_miles, 1),
            "bearing_compass": computed.bearing_compass,
            "approach_state": computed.approach_state.value,
            "data_quality": computed.data_quality.value,
            "selection_score": round(candidate.computed.selection_score or 0, 2),
        }
