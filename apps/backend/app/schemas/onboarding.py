from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator


DesiredRole = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=255)]


class RoleStepRequest(BaseModel):
    desired_role: DesiredRole


def _normalize_countries(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        code = value.strip().upper()
        if len(code) != 2 or not code.isalpha():
            raise ValueError(f"invalid country code: {value!r}")
        if code not in normalized:
            normalized.append(code)
    return normalized


class PreferencesStepRequest(BaseModel):
    home_label: str | None = Field(default=None, max_length=255)
    home_city: str | None = Field(default=None, max_length=120)
    home_country_code: str | None = Field(default=None, min_length=2, max_length=2)
    home_latitude: float | None = Field(default=None, ge=-90, le=90)
    home_longitude: float | None = Field(default=None, ge=-180, le=180)
    travel_radius_km: int | None = Field(default=None, ge=0, le=32767)
    accepts_onsite: bool = False
    accepts_hybrid: bool = False
    accepts_remote: bool = False
    accepts_full_time: bool = True
    accepts_part_time: bool = False
    onsite_countries: list[str] = Field(default_factory=list)
    remote_countries: list[str] = Field(default_factory=list)

    @field_validator("home_label", "home_city")
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("home_country_code")
    @classmethod
    def normalize_country_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if len(normalized) != 2 or not normalized.isalpha():
            raise ValueError("country code must contain two letters")
        return normalized

    @field_validator("onsite_countries", "remote_countries")
    @classmethod
    def normalize_country_list(cls, value: list[str]) -> list[str]:
        return _normalize_countries(value)

    @model_validator(mode="after")
    def validate_choices(self) -> "PreferencesStepRequest":
        if not (self.accepts_onsite or self.accepts_hybrid or self.accepts_remote):
            raise ValueError("select at least one work mode")
        if not (self.accepts_full_time or self.accepts_part_time):
            raise ValueError("select at least one employment type")

        if self.accepts_onsite or self.accepts_hybrid:
            missing = [
                name
                for name, value in (
                    ("home_label", self.home_label),
                    ("home_city", self.home_city),
                    ("home_country_code", self.home_country_code),
                    ("home_latitude", self.home_latitude),
                    ("home_longitude", self.home_longitude),
                    ("travel_radius_km", self.travel_radius_km),
                )
                if value is None
            ]
            if missing:
                raise ValueError(
                    "home location and travel radius are required for on-site or hybrid work"
                )
            if not self.onsite_countries:
                raise ValueError("select at least one on-site country")

        if self.accepts_remote and not self.remote_countries:
            raise ValueError("select at least one remote country")

        return self


class FactsResponse(BaseModel):
    facts_status: Literal["pending", "queued", "ready", "review", "error"] | None
    facts_schema_version: str | None
    facts: dict[str, Any]
    evidence: dict[str, Any]


class GeocodeResult(BaseModel):
    country_code: str
    postal_code: str
    city: str | None
    latitude: float
    longitude: float


class CVStatusResponse(BaseModel):
    id: UUID
    original_filename: str
    byte_size: int
    page_count: int | None
    detected_language: Literal["de", "en", "other"] | None
    extraction_status: Literal["pending", "processing", "ready", "error"]
    extraction_method: Literal["native", "ocr", "mixed"] | None
    extraction_error_code: str | None
    facts_status: Literal["pending", "queued", "ready", "review", "error"]
    created_at: datetime


class OnboardingStepsResponse(BaseModel):
    role: bool
    preferences: bool
    cv: bool


class OnboardingResponse(BaseModel):
    status: Literal["incomplete", "processing", "ready", "error"]
    desired_role: str | None
    home_label: str | None
    home_city: str | None
    home_country_code: str | None
    home_latitude: float | None
    home_longitude: float | None
    travel_radius_km: int | None
    accepts_onsite: bool
    accepts_hybrid: bool
    accepts_remote: bool
    accepts_full_time: bool
    accepts_part_time: bool
    onsite_countries: list[str]
    remote_countries: list[str]
    steps: OnboardingStepsResponse
    cv: CVStatusResponse | None
