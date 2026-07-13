import asyncio

from bw_flight_tracker.providers.mock import MockAircraftProvider


def test_mock_provider_supports_no_flights_scenario() -> None:
    provider = MockAircraftProvider("no_flights")
    assert asyncio.run(provider.fetch_aircraft()) == []


def test_mock_provider_recovery_starts_stale_then_recovers() -> None:
    provider = MockAircraftProvider("provider_recovery")
    first = asyncio.run(provider.fetch_aircraft())
    second = asyncio.run(provider.fetch_aircraft())
    assert first[0].position_age_seconds > 20
    assert any(aircraft.position_age_seconds <= 20 for aircraft in second)
