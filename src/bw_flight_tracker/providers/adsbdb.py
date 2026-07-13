from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote

import httpx

from bw_flight_tracker.config import Settings
from bw_flight_tracker.domain.models import AircraftState, EnrichedFlight


@dataclass
class _CacheEntry:
    value: EnrichedFlight | None
    expires_at_utc: datetime


class AdsbdbEnrichmentProvider:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 5,
    ) -> None:
        self.settings = settings
        self.client = client
        self.timeout_seconds = timeout_seconds
        self.cache: dict[str, _CacheEntry] = {}

    async def enrich(self, aircraft: AircraftState) -> EnrichedFlight | None:
        cache_key = f"{aircraft.icao_hex}:{aircraft.callsign or ''}"
        now = datetime.now(UTC)
        cached = self.cache.get(cache_key)
        if cached and cached.expires_at_utc > now:
            return cached.value

        value = await self._fetch_enrichment(aircraft)
        self.cache[cache_key] = _CacheEntry(
            value,
            now + timedelta(seconds=self.settings.enrichment_cache_seconds),
        )
        return value

    async def _fetch_enrichment(self, aircraft: AircraftState) -> EnrichedFlight | None:
        aircraft_payload: dict[str, Any] | None = None
        route_payload: dict[str, Any] | None = None
        if self.client is not None:
            aircraft_payload = await self._get_optional(self.client, self._aircraft_url(aircraft))
            if aircraft.callsign:
                route_payload = await self._get_optional(self.client, self._callsign_url(aircraft))
        else:
            async with httpx.AsyncClient(verify=self._verify_setting()) as client:
                aircraft_payload = await self._get_optional(client, self._aircraft_url(aircraft))
                if aircraft.callsign:
                    route_payload = await self._get_optional(client, self._callsign_url(aircraft))

        if aircraft_payload is None and route_payload is None:
            return None
        return self._parse_enrichment(aircraft, aircraft_payload or {}, route_payload or {})

    async def _get_optional(self, client: httpx.AsyncClient, url: str) -> dict[str, Any] | None:
        try:
            response = await client.get(url, timeout=self.timeout_seconds)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            payload = response.json()
            return payload if isinstance(payload, dict) else None
        except httpx.HTTPError:
            return None

    def _aircraft_url(self, aircraft: AircraftState) -> str:
        return f"{self.settings.adsbdb_base_url.rstrip('/')}/aircraft/{aircraft.icao_hex}"

    def _callsign_url(self, aircraft: AircraftState) -> str:
        callsign = quote((aircraft.callsign or "").strip())
        return f"{self.settings.adsbdb_base_url.rstrip('/')}/callsign/{callsign}"

    def _verify_setting(self) -> bool | str:
        if self.settings.adsbdb_ca_bundle:
            return self.settings.adsbdb_ca_bundle
        return self.settings.adsbdb_verify_tls

    def _parse_enrichment(
        self,
        aircraft: AircraftState,
        aircraft_payload: dict[str, Any],
        route_payload: dict[str, Any],
    ) -> EnrichedFlight:
        aircraft_details = _nested_response(aircraft_payload, "aircraft")
        route = _nested_response(route_payload, "flightroute")
        airline = _dict_or_empty(route.get("airline"))
        origin = _dict_or_empty(route.get("origin"))
        destination = _dict_or_empty(route.get("destination"))

        manufacturer, model = _split_aircraft_type(_string_or_none(aircraft_details.get("type")))
        return EnrichedFlight(
            provider="adsbdb",
            retrieved_at_utc=datetime.now(UTC),
            airline_name=_string_or_none(airline.get("name")),
            flight_identifier=_string_or_none(route.get("callsign")) or aircraft.callsign,
            origin_iata=_iata(origin),
            destination_iata=_iata(destination),
            origin_city=_city(origin),
            destination_city=_city(destination),
            manufacturer=manufacturer,
            model=model
            or _string_or_none(aircraft_details.get("icao_type"))
            or aircraft.aircraft_type_code,
            registration=_string_or_none(aircraft_details.get("registration"))
            or aircraft.registration,
            confidence="partial" if aircraft_details or route else "unavailable",
        )


def _nested_response(payload: dict[str, Any], key: str) -> dict[str, Any]:
    response = _dict_or_empty(payload.get("response"))
    return _dict_or_empty(response.get(key) or payload.get(key))


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_or_none(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _iata(airport: dict[str, Any]) -> str | None:
    return _string_or_none(airport.get("iata_code") or airport.get("iata"))


def _city(airport: dict[str, Any]) -> str | None:
    return _string_or_none(airport.get("municipality") or airport.get("city"))


def _split_aircraft_type(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    parts = value.split(maxsplit=1)
    if len(parts) == 1:
        return None, parts[0]
    return parts[0], parts[1]
