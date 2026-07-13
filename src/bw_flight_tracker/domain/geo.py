import math

EARTH_RADIUS_MILES = 3958.7613
COMPASS_16 = (
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
)


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def initial_bearing_degrees(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_lambda = math.radians(lon2 - lon1)
    y = math.sin(d_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(d_lambda)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def compass_point(bearing: float) -> str:
    return COMPASS_16[int((bearing + 11.25) // 22.5) % 16]


def project_closest_approach(
    home_lat: float,
    home_lon: float,
    aircraft_lat: float,
    aircraft_lon: float,
    track_degrees: float | None,
    speed_knots: float | None,
    horizon_seconds: int = 900,
) -> tuple[float, float] | None:
    if track_degrees is None or speed_knots is None or speed_knots < 1:
        return None
    miles_per_second = speed_knots * 1.150779 / 3600
    lat_miles = (aircraft_lat - home_lat) * 69.0
    lon_miles = (aircraft_lon - home_lon) * 69.0 * math.cos(math.radians(home_lat))
    theta = math.radians(track_degrees)
    vx = math.sin(theta) * miles_per_second
    vy = math.cos(theta) * miles_per_second
    denom = vx * vx + vy * vy
    if denom == 0:
        return None
    t = max(0.0, min(horizon_seconds, -((lon_miles * vx + lat_miles * vy) / denom)))
    closest = math.hypot(lon_miles + vx * t, lat_miles + vy * t)
    return closest, t


def display_distance(distance: float) -> str:
    return f"{distance:.1f} mi" if distance < 10 else f"{distance:.0f} mi"
