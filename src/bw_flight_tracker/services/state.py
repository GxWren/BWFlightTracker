from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from bw_flight_tracker.config import Settings
from bw_flight_tracker.domain.models import EnrichedFlight, FlightCandidate
from bw_flight_tracker.domain.primary_selection import PrimarySelectionEngine
from bw_flight_tracker.domain.selection import compute_candidate, eligible_candidates
from bw_flight_tracker.providers.mock import MockAircraftProvider, MockEnrichmentProvider


@dataclass
class ManualSelection:
    icao_hex: str
    expires_at_utc: datetime


class StateService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider = MockAircraftProvider(settings.mock_scenario)
        self.enrichment = MockEnrichmentProvider()
        self.manual_by_session: dict[str, ManualSelection] = {}
        self.last_update: datetime | None = None
        self.selector = PrimarySelectionEngine(
            minimum_hold_seconds=settings.automatic_hold_seconds,
            switch_improvement_ratio=settings.switch_improvement_ratio,
        )

    async def current_state(self, session_id: str | None = None) -> dict[str, object]:
        now = datetime.now(UTC)
        aircraft = await self.provider.fetch_aircraft()
        candidates = [
            compute_candidate(a, self.settings.home_latitude, self.settings.home_longitude)
            for a in aircraft
        ]
        eligible = eligible_candidates(
            candidates,
            self.settings.detection_radius_miles,
            max_position_age_seconds=self.settings.stale_position_seconds,
        )
        enriched = {c.aircraft.icao_hex: await self.enrichment.enrich(c.aircraft) for c in eligible}
        selection_mode = "automatic"
        selection_reason = "automatic selection"
        primary = self._manual_candidate(session_id, eligible, now)
        if primary is not None:
            selection_mode = "manual"
            selection_reason = "session manual override active"
        else:
            result = self.selector.select(eligible, now)
            primary = result.candidate
            selection_reason = result.reason

        self.last_update = now
        return {
            "status": "ok" if eligible else "waiting",
            "updated_at_utc": self.last_update.isoformat(),
            "provider": {
                "name": self.settings.aircraft_provider,
                "scenario": self.settings.mock_scenario,
                "stale": bool(aircraft and not eligible),
            },
            "selection_mode": selection_mode,
            "selection_reason": selection_reason,
            "primary": self._serialize(
                primary, enriched.get(primary.aircraft.icao_hex) if primary else None
            )
            if primary
            else None,
            "nearby": [self._serialize(c, enriched.get(c.aircraft.icao_hex)) for c in eligible],
        }

    def select_manual(self, session_id: str, icao_hex: str) -> None:
        self.manual_by_session[session_id] = ManualSelection(
            icao_hex.lower(),
            datetime.now(UTC) + timedelta(seconds=self.settings.manual_selection_seconds),
        )

    def resume_auto(self, session_id: str) -> None:
        self.manual_by_session.pop(session_id, None)

    def _manual_candidate(
        self,
        session_id: str | None,
        eligible: list[FlightCandidate],
        now: datetime,
    ) -> FlightCandidate | None:
        if not session_id:
            return None
        manual = self.manual_by_session.get(session_id)
        if manual is None:
            return None
        if manual.expires_at_utc <= now:
            self.manual_by_session.pop(session_id, None)
            return None
        candidate = next((c for c in eligible if c.aircraft.icao_hex == manual.icao_hex), None)
        if candidate is None:
            self.manual_by_session.pop(session_id, None)
        return candidate

    def _serialize(
        self,
        candidate: FlightCandidate,
        enrichment: EnrichedFlight | None,
    ) -> dict[str, object]:
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
