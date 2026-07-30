from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator


DesiredRole = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=255)]


class RoleStepRequest(BaseModel):
    desired_role: DesiredRole


class PreferencesStepRequest(BaseModel):
    home_label: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=255)]
    home_city: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    home_country_code: str = Field(min_length=2, max_length=2)
    home_latitude: float = Field(ge=-90, le=90)
    home_longitude: float = Field(ge=-180, le=180)
    travel_radius_km: int | None = Field(default=None, ge=0, le=32767)
    accepts_onsite: bool = False
    accepts_hybrid: bool = False
    accepts_remote: bool = False
    accepts_full_time: bool = True
    accepts_part_time: bool = False

    @field_validator("home_country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized.isalpha():
            raise ValueError("country code must contain two letters")
        return normalized

    @model_validator(mode="after")
    def validate_choices(self) -> "PreferencesStepRequest":
        if not (self.accepts_onsite or self.accepts_hybrid or self.accepts_remote):
            raise ValueError("select at least one work mode")
        if not (self.accepts_full_time or self.accepts_part_time):
            raise ValueError("select at least one employment type")
        if (self.accepts_onsite or self.accepts_hybrid) and self.travel_radius_km is None:
            raise ValueError("travel radius is required for on-site or hybrid work")
        return self


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
    steps: OnboardingStepsResponse
    cv: CVStatusResponse | None
