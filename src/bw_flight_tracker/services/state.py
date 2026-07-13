from datetime import UTC, datetime
from typing import Any, Protocol

import httpx

from bw_flight_tracker.config import Settings
from bw_flight_tracker.domain.models import AircraftState, EnrichedFlight, FlightCandidate
from bw_flight_tracker.domain.primary_selection import PrimarySelectionEngine
from bw_flight_tracker.domain.selection import compute_candidate, eligible_candidates
from bw_flight_tracker.providers.adsbdb import AdsbdbEnrichmentProvider
from bw_flight_tracker.providers.airplanes_live import AirplanesLiveProvider
from bw_flight_tracker.providers.mock import MockAircraftProvider, MockEnrichmentProvider


class EnrichmentProvider(Protocol):
    async def enrich(self, aircraft: AircraftState) -> EnrichedFlight | None: ...


class StateService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider = (
            AirplanesLiveProvider(settings)
            if settings.aircraft_provider == "airplanes_live"
            else MockAircraftProvider(settings.mock_scenario)
        )
        self.enrichment = self._build_enrichment_provider(settings)
        self.manual_icao_by_viewer: dict[str, str] = {}
        self.selection_engine = PrimarySelectionEngine(
            minimum_hold_seconds=settings.automatic_hold_seconds,
            switch_improvement_ratio=settings.switch_improvement_ratio,
        )
        self.last_update: datetime | None = None

    async def current_state(self, viewer_id: str = "default") -> dict[str, object]:
        provider_error: str | None = None
        try:
            aircraft = await self.provider.fetch_aircraft()
        except httpx.HTTPError:
            aircraft = []
            provider_error = "provider_unavailable"
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
        manual_icao = self.manual_icao_by_viewer.get(viewer_id)
        automatic_selection = self.selection_engine.select(eligible)
        primary = (
            next((c for c in eligible if c.aircraft.icao_hex == manual_icao), None)
            or automatic_selection.candidate
        )
        primary_enrichment = await self._enrich_primary(primary)
        self.last_update = datetime.now(UTC)
        stale = (
            bool(aircraft)
            and not eligible
            and all(a.position_age_seconds > self.settings.stale_position_seconds for a in aircraft)
        )
        return {
            "status": "ok" if primary else "waiting",
            "updated_at_utc": self.last_update.isoformat(),
            "provider": {
                "name": self.settings.aircraft_provider,
                "stale": stale or provider_error is not None,
                "error": provider_error,
            },
            "selection_mode": "manual" if manual_icao and primary else "automatic",
            "primary": self._serialize(primary, primary_enrichment) if primary else None,
            "nearby": [
                self._serialize(c, primary_enrichment if c is primary else None) for c in eligible
            ],
        }

    def _build_enrichment_provider(self, settings: Settings) -> EnrichmentProvider | None:
        if settings.enrichment_provider == "adsbdb":
            return AdsbdbEnrichmentProvider(settings)
        if settings.enrichment_provider == "disabled":
            return None
        return MockEnrichmentProvider()

    async def _enrich_primary(self, primary: FlightCandidate | None) -> EnrichedFlight | None:
        if primary is None or self.enrichment is None:
            return None
        return await self.enrichment.enrich(primary.aircraft)

    def select_manual(self, viewer_id: str, icao_hex: str | None = None) -> None:
        if icao_hex is None:
            icao_hex = viewer_id
            viewer_id = "default"
        self.manual_icao_by_viewer[viewer_id] = icao_hex.lower()

    def resume_auto(self, viewer_id: str = "default") -> None:
        self.manual_icao_by_viewer.pop(viewer_id, None)
        self.selection_engine.reset()

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
