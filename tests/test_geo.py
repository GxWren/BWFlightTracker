from bw_flight_tracker.domain.geo import (
    compass_point,
    haversine_miles,
    initial_bearing_degrees,
    project_closest_approach,
)


def test_haversine_identical_points() -> None:
    assert haversine_miles(41.88, -87.63, 41.88, -87.63) == 0


def test_haversine_city_pair_tolerance() -> None:
    assert 710 < haversine_miles(41.8781, -87.6298, 40.7128, -74.0060) < 725


def test_bearing_and_compass() -> None:
    assert compass_point(initial_bearing_degrees(0, 0, 1, 0)) == "N"
    assert compass_point(initial_bearing_degrees(0, 0, 0, 1)) == "E"


def test_project_closest_approach_crossing_track() -> None:
    closest = project_closest_approach(0, 0, 0, -1, 90, 600)
    assert closest is not None
    assert closest[0] < 1
    assert closest[1] > 0
