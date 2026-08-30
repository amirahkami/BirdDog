import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Numeric, SmallInteger, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_profiles"
    __table_args__ = (
        CheckConstraint(
            "onboarding_status IN ('incomplete', 'processing', 'ready', 'error')",
            name="onboarding_status",
        ),
        CheckConstraint(
            "home_latitude IS NULL OR home_latitude BETWEEN -90 AND 90",
            name="home_latitude",
        ),
        CheckConstraint(
            "home_longitude IS NULL OR home_longitude BETWEEN -180 AND 180",
            name="home_longitude",
        ),
        CheckConstraint(
            "(home_latitude IS NULL) = (home_longitude IS NULL)",
            name="home_coordinates_pair",
        ),
        CheckConstraint(
            "travel_radius_km IS NULL OR travel_radius_km >= 0",
            name="travel_radius_km",
        ),
        CheckConstraint(
            "onboarding_status <> 'ready' OR (accepts_onsite OR accepts_hybrid OR accepts_remote)",
            name="ready_work_mode",
        ),
        CheckConstraint(
            "onboarding_status <> 'ready' OR (accepts_full_time OR accepts_part_time)",
            name="ready_employment_type",
        ),
        CheckConstraint(
            "onboarding_status <> 'ready' OR (desired_role_text IS NOT NULL AND btrim(desired_role_text) <> '' "
            "AND (NOT (accepts_onsite OR accepts_hybrid) OR (home_country_code IS NOT NULL AND home_latitude IS NOT NULL)))",
            name="ready_identity",
        ),
        CheckConstraint(
            "onboarding_status <> 'ready' OR NOT (accepts_onsite OR accepts_hybrid) OR travel_radius_km IS NOT NULL",
            name="ready_radius",
        ),
        CheckConstraint(
            "onboarding_status <> 'ready' OR NOT (accepts_onsite OR accepts_hybrid) OR array_length(onsite_countries, 1) >= 1",
            name="ready_onsite_countries",
        ),
        CheckConstraint(
            "onboarding_status <> 'ready' OR NOT accepts_remote OR array_length(remote_countries, 1) >= 1",
            name="ready_remote_countries",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    desired_role_text: Mapped[str | None] = mapped_column(String(255))
    home_label: Mapped[str | None] = mapped_column(String(255))
    home_city: Mapped[str | None] = mapped_column(String(120))
    home_country_code: Mapped[str | None] = mapped_column(String(2))
    home_latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    home_longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    travel_radius_km: Mapped[int | None] = mapped_column(SmallInteger)
    accepts_onsite: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    accepts_hybrid: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    accepts_remote: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    accepts_full_time: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    accepts_part_time: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    onsite_countries: Mapped[list[str]] = mapped_column(
        ARRAY(String(2)), nullable=False, server_default="{}"
    )
    remote_countries: Mapped[list[str]] = mapped_column(
        ARRAY(String(2)), nullable=False, server_default="{}"
    )
    onboarding_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="incomplete", server_default="incomplete"
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
