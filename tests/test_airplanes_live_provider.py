import asyncio

import httpx

from bw_flight_tracker.config import Settings
from bw_flight_tracker.providers.airplanes_live import AirplanesLiveProvider


def test_airplanes_live_provider_maps_point_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).endswith("/point/41.88/-87.63/9")
        return httpx.Response(
            200,
            json={
                "now": 1_734_000_000,
                "total": 1,
                "aircraft": [
                    {
                        "hex": " A1B2C3 ",
                        "flight": " ual123 ",
                        "lat": 41.9,
                        "lon": -87.65,
                        "alt_baro": 7200,
                        "gs": 211.5,
                        "track": 151.2,
                        "baro_rate": -320,
                        "seen_pos": 2.4,
                        "seen": 1.2,
                        "r": " n123ua ",
                        "t": "B738",
                        "desc": "Boeing 737-800",
                        "type": "adsb_icao",
                    }
                ],
            },
        )

    settings = Settings(
        aircraft_provider="airplanes_live",
        airplanes_live_base_url="https://api.airplanes.live/v2/",
        home_latitude=41.88,
        home_longitude=-87.63,
        detection_radius_miles=10,
    )
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = AirplanesLiveProvider(settings, client)

    try:
        aircraft = asyncio.run(provider.fetch_aircraft())
    finally:
        asyncio.run(client.aclose())

    assert len(aircraft) == 1
    mapped = aircraft[0]
    assert mapped.icao_hex == "a1b2c3"
    assert mapped.callsign == "UAL123"
    assert mapped.registration == "N123UA"
    assert mapped.altitude_ft == 7200
    assert mapped.ground_speed_knots == 211.5
    assert mapped.track_degrees == 151.2
    assert mapped.vertical_rate_fpm == -320
    assert mapped.position_age_seconds == 2.4
    assert mapped.message_age_seconds == 1.2
    assert mapped.source_type == "adsb_icao"


def test_airplanes_live_provider_skips_rows_without_position() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "aircraft": [
                    {"hex": "a", "lat": 41.9},
                    {"hex": "b", "lat": 41.9, "lon": -87.65, "alt_baro": "ground"},
                ]
            },
        )

    settings = Settings(aircraft_provider="airplanes_live")
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = AirplanesLiveProvider(settings, client)

    try:
        aircraft = asyncio.run(provider.fetch_aircraft())
    finally:
        asyncio.run(client.aclose())

    assert len(aircraft) == 1
    assert aircraft[0].icao_hex == "b"
    assert aircraft[0].altitude_ft == 0
    assert aircraft[0].on_ground is True


def test_airplanes_live_provider_accepts_live_ac_payload_key() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"ac": [{"hex": "a1b2c3", "lat": 41.9, "lon": -87.65, "seen_pos": 1}]},
        )

    settings = Settings(aircraft_provider="airplanes_live")
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = AirplanesLiveProvider(settings, client)

    try:
        aircraft = asyncio.run(provider.fetch_aircraft())
    finally:
        asyncio.run(client.aclose())

    assert len(aircraft) == 1
    assert aircraft[0].icao_hex == "a1b2c3"


def test_airplanes_live_provider_uses_ca_bundle_before_verify_flag() -> None:
    settings = Settings(
        aircraft_provider="airplanes_live",
        airplanes_live_ca_bundle="C:/certs/company.pem",
        airplanes_live_verify_tls=False,
    )
    provider = AirplanesLiveProvider(settings)

    assert provider._verify_setting() == "C:/certs/company.pem"  # noqa: SLF001


def test_airplanes_live_provider_can_disable_tls_verification() -> None:
    settings = Settings(aircraft_provider="airplanes_live", airplanes_live_verify_tls=False)
    provider = AirplanesLiveProvider(settings)

    assert provider._verify_setting() is False  # noqa: SLF001
