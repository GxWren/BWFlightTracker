from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ApproachState(StrEnum):
    APPROACHING = "approaching"
    PASSING = "passing"
    DEPARTING = "departing"
    INDETERMINATE = "indeterminate"


class CommercialClassification(StrEnum):
    COMMERCIAL = "commercial"
    NONCOMMERCIAL = "noncommercial"
    UNKNOWN = "unknown"


class DataQuality(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class AircraftState:
    icao_hex: str
    latitude: float
    longitude: float
    observed_at_utc: datetime = field(default_factory=lambda: datetime.now(UTC))
    callsign: str | None = None
    registration: str | None = None
    aircraft_type_code: str | None = None
    aircraft_description: str | None = None
    altitude_ft: int | None = None
    ground_speed_knots: float | None = None
    track_degrees: float | None = None
    vertical_rate_fpm: int | None = None
    on_ground: bool = False
    position_age_seconds: float = 0
    message_age_seconds: float | None = None
    source_type: str | None = None
    emergency_status: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "icao_hex", self.icao_hex.lower().strip())
        if self.callsign:
            object.__setattr__(self, "callsign", self.callsign.strip().upper())
        if self.registration:
            object.__setattr__(self, "registration", self.registration.strip().upper())


@dataclass(frozen=True)
class EnrichedFlight:
    provider: str
    retrieved_at_utc: datetime
    airline_name: str | None = None
    flight_identifier: str | None = None
    origin_iata: str | None = None
    destination_iata: str | None = None
    origin_city: str | None = None
    destination_city: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    registration: str | None = None
    confidence: str = "unavailable"


@dataclass(frozen=True)
class ComputedFlightState:
    horizontal_distance_miles: float
    bearing_degrees: float
    bearing_compass: str
    approach_state: ApproachState
    estimated_closest_distance_miles: float | None
    estimated_seconds_to_closest_approach: float | None
    selection_score: float | None
    selection_reason: dict[str, float | str]
    commercial_classification: CommercialClassification
    data_quality: DataQuality


@dataclass(frozen=True)
class FlightCandidate:
    aircraft: AircraftState
    computed: ComputedFlightState
    enrichment: EnrichedFlight | None = None
