import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, cast


@dataclass(frozen=True)
class SecretValue:
    value: str

    def get_secret_value(self) -> str:
        return self.value

    def __str__(self) -> str:
        return "**********"


@dataclass(frozen=True)
class Settings:
    app_env: Literal["development", "test", "production"] = "development"
    app_base_url: str = "http://localhost:8000"
    database_url: str = "sqlite:///./data/bw_flight_tracker.db"
    aircraft_provider: Literal["mock", "airplanes_live"] = "mock"
    airplanes_live_base_url: str = "https://api.airplanes.live/v2/"
    enrichment_provider: Literal["mock", "disabled", "adsbdb"] = "mock"
    adsbdb_base_url: str = "https://api.adsbdb.com/v0/"
    geocoder_provider: str = "disabled"
    geocoder_api_key: SecretValue | None = None
    admin_token: SecretValue | None = None
    secret_key: SecretValue = SecretValue("change-me-for-local-development")
    log_level: str = "INFO"
    scheduler_enabled: bool = True
    time_zone: str = "America/Chicago"
    home_latitude: float = 41.88
    home_longitude: float = -87.63
    detection_radius_miles: float = 10
    min_altitude_ft: int = 1000
    max_altitude_ft: int = 60000
    stale_position_seconds: float = 20
    manual_selection_seconds: int = 60
    automatic_hold_seconds: int = 15
    switch_improvement_ratio: float = 0.25
    mock_scenario: str = "multiple_competing"
    sse_heartbeat_seconds: int = 20

    def __post_init__(self) -> None:
        if self.app_env not in {"development", "test", "production"}:
            raise ValueError("APP_ENV must be development, test, or production")
        if self.aircraft_provider not in {"mock", "airplanes_live"}:
            raise ValueError("AIRCRAFT_PROVIDER must be mock or airplanes_live")
        if self.enrichment_provider not in {"mock", "disabled", "adsbdb"}:
            raise ValueError("ENRICHMENT_PROVIDER must be mock, disabled, or adsbdb")
        if not 1 <= self.detection_radius_miles <= 50:
            raise ValueError("DETECTION_RADIUS_MILES must be between 1 and 50")
        if not 5 <= self.stale_position_seconds <= 120:
            raise ValueError("STALE_POSITION_SECONDS must be between 5 and 120")


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_env=cast(
            Literal["development", "test", "production"], _literal_env("APP_ENV", "development")
        ),
        app_base_url=os.getenv("APP_BASE_URL", "http://localhost:8000"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./data/bw_flight_tracker.db"),
        aircraft_provider=cast(
            Literal["mock", "airplanes_live"], _literal_env("AIRCRAFT_PROVIDER", "mock")
        ),
        airplanes_live_base_url=os.getenv(
            "AIRPLANES_LIVE_BASE_URL", "https://api.airplanes.live/v2/"
        ),
        enrichment_provider=cast(
            Literal["mock", "disabled", "adsbdb"], _literal_env("ENRICHMENT_PROVIDER", "mock")
        ),
        adsbdb_base_url=os.getenv("ADSBDB_BASE_URL", "https://api.adsbdb.com/v0/"),
        geocoder_provider=os.getenv("GEOCODER_PROVIDER", "disabled"),
        geocoder_api_key=_secret_env("GEOCODER_API_KEY"),
        admin_token=_secret_env("ADMIN_TOKEN"),
        secret_key=SecretValue(os.getenv("SECRET_KEY", "change-me-for-local-development")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        scheduler_enabled=_bool_env("SCHEDULER_ENABLED", True),
        time_zone=os.getenv("TIME_ZONE", "America/Chicago"),
        home_latitude=_float_env("HOME_LATITUDE", 41.88),
        home_longitude=_float_env("HOME_LONGITUDE", -87.63),
        detection_radius_miles=_float_env("DETECTION_RADIUS_MILES", 10),
        min_altitude_ft=_int_env("MIN_ALTITUDE_FT", 1000),
        max_altitude_ft=_int_env("MAX_ALTITUDE_FT", 60000),
        stale_position_seconds=_float_env("STALE_POSITION_SECONDS", 20),
        manual_selection_seconds=_int_env("MANUAL_SELECTION_SECONDS", 60),
        automatic_hold_seconds=_int_env("AUTOMATIC_HOLD_SECONDS", 15),
        switch_improvement_ratio=_float_env("SWITCH_IMPROVEMENT_RATIO", 0.25),
        mock_scenario=os.getenv("MOCK_SCENARIO", "multiple_competing"),
        sse_heartbeat_seconds=_int_env("SSE_HEARTBEAT_SECONDS", 20),
    )


def _secret_env(name: str) -> SecretValue | None:
    value = os.getenv(name)
    return SecretValue(value) if value else None


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value is not None else default


def _literal_env(name: str, default: str) -> str:
    return os.getenv(name, default)
