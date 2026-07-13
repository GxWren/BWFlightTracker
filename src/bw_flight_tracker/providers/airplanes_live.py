from datetime import UTC, datetime
from math import ceil
from typing import Any

import httpx

from bw_flight_tracker.config import Settings
from bw_flight_tracker.domain.models import AircraftState


class AirplanesLiveProvider:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 5,
    ) -> None:
        self.settings = settings
        self.client = client
        self.timeout_seconds = timeout_seconds

    async def fetch_aircraft(self) -> list[AircraftState]:
        url = self._point_url()
        if self.client is not None:
            response = await self.client.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            return self._parse_payload(response.json())

        async with httpx.AsyncClient(verify=self._verify_setting()) as client:
            response = await client.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            return self._parse_payload(response.json())

    def _point_url(self) -> str:
        base_url = self.settings.airplanes_live_base_url.rstrip("/")
        return (
            f"{base_url}/point/"
            f"{_format_number(self.settings.home_latitude)}/"
            f"{_format_number(self.settings.home_longitude)}/"
            f"{_format_number(self._request_radius_nautical_miles())}"
        )

    def _request_radius_nautical_miles(self) -> int:
        return min(250, ceil(self.settings.detection_radius_miles / 1.150779))

    def _verify_setting(self) -> bool | str:
        if self.settings.airplanes_live_ca_bundle:
            return self.settings.airplanes_live_ca_bundle
        return self.settings.airplanes_live_verify_tls

    def _parse_payload(self, payload: dict[str, Any]) -> list[AircraftState]:
        now = datetime.now(UTC)
        aircraft_rows = payload.get("aircraft", payload.get("ac", []))
        if not isinstance(aircraft_rows, list):
            return []

        aircraft = []
        for row in aircraft_rows:
            if not isinstance(row, dict):
                continue
            state = self._parse_aircraft(row, now)
            if state is not None:
                aircraft.append(state)
        return aircraft

    def _parse_aircraft(self, row: dict[str, Any], now: datetime) -> AircraftState | None:
        icao_hex = _string_or_none(row.get("hex"))
        latitude = _float_or_none(row.get("lat"))
        longitude = _float_or_none(row.get("lon"))
        if icao_hex is None or latitude is None or longitude is None:
            return None

        altitude = _altitude_or_none(row.get("alt_baro"))
        position_age = _float_or_none(row.get("seen_pos"))
        message_age = _float_or_none(row.get("seen"))
        return AircraftState(
            icao_hex=icao_hex,
            latitude=latitude,
            longitude=longitude,
            observed_at_utc=now,
            callsign=_string_or_none(row.get("flight")),
            registration=_string_or_none(row.get("r")),
            aircraft_type_code=_string_or_none(row.get("t")),
            aircraft_description=_string_or_none(row.get("desc")),
            altitude_ft=altitude,
            ground_speed_knots=_float_or_none(row.get("gs")),
            track_degrees=_float_or_none(row.get("track")),
            vertical_rate_fpm=_int_or_none(row.get("baro_rate")),
            on_ground=row.get("alt_baro") == "ground",
            position_age_seconds=position_age if position_age is not None else 999,
            message_age_seconds=message_age,
            source_type=_source_type(row),
            emergency_status=_string_or_none(row.get("emergency")),
        )


def _string_or_none(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _format_number(value: float) -> str:
    return f"{value:g}"


def _float_or_none(value: Any) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    return None


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return round(value)
    return None


def _altitude_or_none(value: Any) -> int | None:
    if value == "ground":
        return 0
    return _int_or_none(value)


def _source_type(row: dict[str, Any]) -> str | None:
    if row.get("type"):
        return _string_or_none(row.get("type"))
    if row.get("mlat"):
        return "mlat"
    if row.get("tisb"):
        return "tisb"
    return "adsb"
