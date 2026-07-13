from datetime import UTC, datetime

from bw_flight_tracker.domain.models import AircraftState, CommercialClassification
from bw_flight_tracker.domain.selection import (
    classify_commercial,
    compute_candidate,
    eligible_candidates,
)


def test_commercial_classification_uses_known_prefix() -> None:
    aircraft = AircraftState("ABC123", 41.9, -87.6, datetime.now(UTC), callsign=" ual123 ")
    assert classify_commercial(aircraft) == CommercialClassification.COMMERCIAL


def test_registration_like_callsign_is_noncommercial() -> None:
    aircraft = AircraftState("ABC123", 41.9, -87.6, datetime.now(UTC), callsign="N123AB")
    assert classify_commercial(aircraft) == CommercialClassification.NONCOMMERCIAL


def test_eligible_filters_to_commercial_inside_radius() -> None:
    commercial = compute_candidate(
        AircraftState(
            "a",
            41.89,
            -87.64,
            datetime.now(UTC),
            callsign="DAL12",
            altitude_ft=5000,
            ground_speed_knots=200,
            track_degrees=180,
        ),
        41.88,
        -87.63,
    )
    private = compute_candidate(
        AircraftState(
            "b",
            41.89,
            -87.64,
            datetime.now(UTC),
            callsign="N12AB",
            altitude_ft=5000,
            ground_speed_knots=200,
            track_degrees=180,
        ),
        41.88,
        -87.63,
    )
    assert [c.aircraft.icao_hex for c in eligible_candidates([private, commercial], 10)] == ["a"]


def test_eligible_excludes_grounded_aircraft() -> None:
    grounded = compute_candidate(
        AircraftState(
            "g",
            41.89,
            -87.64,
            datetime.now(UTC),
            callsign="AAL123",
            altitude_ft=0,
            on_ground=True,
            position_age_seconds=1,
        ),
        41.88,
        -87.63,
    )

    assert eligible_candidates([grounded], 10) == []
