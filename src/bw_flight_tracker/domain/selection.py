from collections.abc import Iterable

from bw_flight_tracker.domain.geo import (
    compass_point,
    haversine_miles,
    initial_bearing_degrees,
    project_closest_approach,
)
from bw_flight_tracker.domain.models import (
    AircraftState,
    ApproachState,
    CommercialClassification,
    ComputedFlightState,
    DataQuality,
    FlightCandidate,
)

AIRLINE_PREFIXES = {
    "AAL",
    "DAL",
    "UAL",
    "SWA",
    "JBU",
    "ASA",
    "FFT",
    "NKS",
    "BAW",
    "DLH",
    "ACA",
    "FDX",
    "UPS",
}


def classify_commercial(aircraft: AircraftState) -> CommercialClassification:
    if (
        aircraft.callsign
        and len(aircraft.callsign) >= 3
        and aircraft.callsign[:3] in AIRLINE_PREFIXES
    ):
        return CommercialClassification.COMMERCIAL
    if aircraft.callsign and aircraft.callsign.startswith("N"):
        return CommercialClassification.NONCOMMERCIAL
    return CommercialClassification.UNKNOWN


def data_quality(aircraft: AircraftState) -> DataQuality:
    if (
        aircraft.position_age_seconds <= 10
        and aircraft.ground_speed_knots is not None
        and aircraft.track_degrees is not None
    ):
        return DataQuality.HIGH
    if aircraft.position_age_seconds <= 20:
        return DataQuality.MEDIUM
    return DataQuality.LOW


def compute_candidate(aircraft: AircraftState, home_lat: float, home_lon: float) -> FlightCandidate:
    distance = haversine_miles(home_lat, home_lon, aircraft.latitude, aircraft.longitude)
    bearing = initial_bearing_degrees(home_lat, home_lon, aircraft.latitude, aircraft.longitude)
    closest = project_closest_approach(
        home_lat,
        home_lon,
        aircraft.latitude,
        aircraft.longitude,
        aircraft.track_degrees,
        aircraft.ground_speed_knots,
    )
    closest_distance = closest[0] if closest else distance
    closest_seconds = closest[1] if closest else None
    approach = ApproachState.INDETERMINATE
    if closest_seconds is not None:
        if closest_seconds < 30:
            approach = ApproachState.PASSING
        elif closest_distance < distance:
            approach = ApproachState.APPROACHING
        else:
            approach = ApproachState.DEPARTING
    quality = data_quality(aircraft)
    commercial = classify_commercial(aircraft)
    altitude = aircraft.altitude_ft or 0
    altitude_penalty = max(0.0, (altitude - 15000) / 5000)
    approach_penalty = {
        ApproachState.APPROACHING: -10,
        ApproachState.PASSING: 0,
        ApproachState.INDETERMINATE: 5,
        ApproachState.DEPARTING: 15,
    }[approach]
    quality_penalty = {DataQuality.HIGH: 0, DataQuality.MEDIUM: 5, DataQuality.LOW: 15}[quality]
    score = (
        closest_distance * 10
        + distance * 2
        + altitude_penalty
        + approach_penalty
        + aircraft.position_age_seconds
        + quality_penalty
    )
    reason: dict[str, float | str] = {
        "closest_distance": round(closest_distance, 3),
        "current_distance": round(distance, 3),
        "approach_state": approach.value,
        "position_age": aircraft.position_age_seconds,
        "data_quality": quality.value,
    }
    return FlightCandidate(
        aircraft,
        ComputedFlightState(
            distance,
            bearing,
            compass_point(bearing),
            approach,
            closest_distance,
            closest_seconds,
            score,
            reason,
            commercial,
            quality,
        ),
    )


def eligible_candidates(
    candidates: Iterable[FlightCandidate],
    radius_miles: float,
    commercial_only: bool = True,
    min_altitude_ft: int = 1000,
    max_altitude_ft: int = 60000,
) -> list[FlightCandidate]:
    eligible = []
    for candidate in candidates:
        aircraft = candidate.aircraft
        if aircraft.on_ground:
            continue
        if candidate.computed.horizontal_distance_miles > radius_miles:
            continue
        if (
            not aircraft.on_ground
            and aircraft.altitude_ft is not None
            and not (min_altitude_ft <= aircraft.altitude_ft <= max_altitude_ft)
        ):
            continue
        if (
            commercial_only
            and candidate.computed.commercial_classification != CommercialClassification.COMMERCIAL
        ):
            continue
        eligible.append(candidate)
    return sorted(eligible, key=lambda c: c.computed.horizontal_distance_miles)
