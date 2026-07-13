from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    app_base_url: str = "http://localhost:8000"
    database_url: str = "sqlite:///./data/bw_flight_tracker.db"
    aircraft_provider: Literal["mock", "airplanes_live"] = "mock"
    mock_scenario: Literal[
        "no_flights",
        "one_commercial",
        "multiple_competing",
        "missing_route",
        "private_aircraft",
        "stale_provider",
        "provider_recovery",
    ] = "multiple_competing"
    airplanes_live_base_url: str = "https://api.airplanes.live/v2/"
    airplanes_live_verify_tls: bool = True
    airplanes_live_ca_bundle: str | None = None
    enrichment_provider: Literal["mock", "disabled", "adsbdb"] = "mock"
    adsbdb_base_url: str = "https://api.adsbdb.com/v0/"
    geocoder_provider: str = "disabled"
    geocoder_api_key: SecretStr | None = None
    admin_token: SecretStr | None = None
    secret_key: SecretStr = SecretStr("change-me-for-local-development")
    log_level: str = "INFO"
    scheduler_enabled: bool = True
    time_zone: str = "America/Chicago"
    home_latitude: float = 41.88
    home_longitude: float = -87.63
    detection_radius_miles: float = Field(default=10, ge=1, le=250)
    min_altitude_ft: int = 1000
    max_altitude_ft: int = 60000
    stale_position_seconds: float = Field(default=20, ge=5, le=120)
    manual_selection_seconds: int = 60
    automatic_hold_seconds: int = 15
    switch_improvement_ratio: float = 0.25

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()


@lru_cache
def get_settings() -> Settings:
    return Settings()
