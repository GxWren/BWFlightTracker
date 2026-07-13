from datetime import UTC, datetime
from typing import Any

from bw_flight_tracker.config import Settings
from bw_flight_tracker.domain.models import EnrichedFlight, FlightCandidate
from bw_flight_tracker.domain.primary_selection import PrimarySelectionEngine
from bw_flight_tracker.domain.selection import compute_candidate, eligible_candidates
from bw_flight_tracker.providers.mock import MockAircraftProvider, MockEnrichmentProvider


class StateService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider = MockAircraftProvider(settings.mock_scenario)
        self.enrichment = MockEnrichmentProvider()
        self.manual_icao_by_viewer: dict[str, str] = {}
        self.selection_engine = PrimarySelectionEngine(
            minimum_hold_seconds=settings.automatic_hold_seconds,
            switch_improvement_ratio=settings.switch_improvement_ratio,
        )
        self.last_update: datetime | None = None

    async def current_state(self, viewer_id: str = "default") -> dict[str, object]:
        aircraft = await self.provider.fetch_aircraft()
        fresh_aircraft = [
            a for a in aircraft if a.position_age_seconds <= self.settings.stale_position_seconds
        ]
        candidates = [
            compute_candidate(a, self.settings.home_latitude, self.settings.home_longitude)
            for a in fresh_aircraft
        ]
        eligible = eligible_candidates(
            candidates,
            self.settings.detection_radius_miles,
            min_altitude_ft=self.settings.min_altitude_ft,
            max_altitude_ft=self.settings.max_altitude_ft,
        )
        enriched = {c.aircraft.icao_hex: await self.enrichment.enrich(c.aircraft) for c in eligible}
        manual_icao = self.manual_icao_by_viewer.get(viewer_id)
        automatic_selection = self.selection_engine.select(eligible)
        primary = (
            next((c for c in eligible if c.aircraft.icao_hex == manual_icao), None)
            or automatic_selection.candidate
        )
        self.last_update = datetime.now(UTC)
        stale = (
            bool(aircraft)
            and not eligible
            and all(a.position_age_seconds > self.settings.stale_position_seconds for a in aircraft)
        )
        return {
            "status": "ok" if primary else "waiting",
            "updated_at_utc": self.last_update.isoformat(),
            "provider": {"name": self.settings.aircraft_provider, "stale": stale},
            "selection_mode": "manual" if manual_icao and primary else "automatic",
            "primary": self._serialize(
                primary, enriched.get(primary.aircraft.icao_hex) if primary else None
            )
            if primary
            else None,
            "nearby": [self._serialize(c, enriched.get(c.aircraft.icao_hex)) for c in eligible],
        }

    def select_manual(self, viewer_id: str, icao_hex: str | None = None) -> None:
        if icao_hex is None:
            icao_hex = viewer_id
            viewer_id = "default"
        self.manual_icao_by_viewer[viewer_id] = icao_hex.lower()

    def resume_auto(self, viewer_id: str = "default") -> None:
        self.manual_icao_by_viewer.pop(viewer_id, None)

    def _serialize(
        self, candidate: FlightCandidate, enrichment: EnrichedFlight | None
    ) -> dict[str, Any]:
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
