import asyncio

import httpx

from bw_flight_tracker.config import Settings
from bw_flight_tracker.domain.models import AircraftState
from bw_flight_tracker.providers.adsbdb import AdsbdbEnrichmentProvider


def test_adsbdb_enrichment_combines_aircraft_and_callsign_details() -> None:
    requested_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if "/aircraft/" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "response": {
                        "aircraft": {
                            "registration": "N8794Q",
                            "type": "BOEING 737 MAX 8",
                            "icao_type": "B38M",
                        }
                    }
                },
            )
        return httpx.Response(
            200,
            json={
                "response": {
                    "flightroute": {
                        "callsign": "SWA3569",
                        "airline": {"name": "Southwest Airlines"},
                        "origin": {"iata_code": "DAL", "municipality": "Dallas"},
                        "destination": {"iata_code": "SAT", "municipality": "San Antonio"},
                    }
                }
            },
        )

    settings = Settings(enrichment_provider="adsbdb", enrichment_cache_seconds=900)
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = AdsbdbEnrichmentProvider(settings, client)
    aircraft = AircraftState(
        "ac1ab8",
        29.9,
        -98.6,
        callsign="SWA3569",
        registration="N8794Q",
        aircraft_type_code="B38M",
    )

    try:
        first = asyncio.run(provider.enrich(aircraft))
        second = asyncio.run(provider.enrich(aircraft))
    finally:
        asyncio.run(client.aclose())

    assert first is not None
    assert first.airline_name == "Southwest Airlines"
    assert first.flight_identifier == "SWA3569"
    assert first.origin_iata == "DAL"
    assert first.destination_iata == "SAT"
    assert first.manufacturer == "BOEING"
    assert first.model == "737 MAX 8"
    assert first.registration == "N8794Q"
    assert second is first
    assert len(requested_urls) == 2


def test_adsbdb_enrichment_returns_none_when_details_are_unavailable() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"response": None})

    settings = Settings(enrichment_provider="adsbdb")
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = AdsbdbEnrichmentProvider(settings, client)
    aircraft = AircraftState("ac1ab8", 29.9, -98.6, callsign="SWA3569")

    try:
        enrichment = asyncio.run(provider.enrich(aircraft))
    finally:
        asyncio.run(client.aclose())

    assert enrichment is None
