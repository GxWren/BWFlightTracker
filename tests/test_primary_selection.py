from datetime import UTC, datetime, timedelta

from bw_flight_tracker.domain.models import AircraftState, FlightCandidate
from bw_flight_tracker.domain.primary_selection import PrimarySelectionEngine
from bw_flight_tracker.domain.selection import compute_candidate

HOME_LAT = 41.88
HOME_LON = -87.63


def candidate(icao: str, lat: float, score_hint_track: float = 180) -> FlightCandidate:
    return compute_candidate(
        AircraftState(
            icao,
            lat,
            -87.64,
            datetime.now(UTC),
            callsign="UAL123",
            altitude_ft=5000,
            ground_speed_knots=200,
            track_degrees=score_hint_track,
            position_age_seconds=1,
        ),
        HOME_LAT,
        HOME_LON,
    )


def test_selector_holds_current_primary_during_minimum_hold() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    current = candidate("a", 41.89)
    challenger = candidate("b", 41.881)
    engine = PrimarySelectionEngine(minimum_hold_seconds=15)

    first = engine.select([current], now)
    held = engine.select([challenger, current], now + timedelta(seconds=5))

    assert first.candidate is current
    assert held.candidate is current
    assert held.reason == "minimum hold time active"


def test_selector_requires_two_challenger_cycles_after_hold() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    current = candidate("a", 41.94, score_hint_track=0)
    challenger = candidate("b", 41.881)
    engine = PrimarySelectionEngine(minimum_hold_seconds=1, switch_improvement_ratio=0.25)

    engine.select([current], now)
    pending = engine.select([challenger, current], now + timedelta(seconds=2))
    switched = engine.select([challenger, current], now + timedelta(seconds=12))

    assert pending.candidate is current
    assert pending.reason == "challenger pending hysteresis confirmation"
    assert switched.candidate is challenger
    assert switched.reason == "challenger cleared hysteresis"
