import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CanonicalJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "canonical_jobs"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'unavailable')", name="status"),
        CheckConstraint(
            "language IS NULL OR language IN ('de', 'en', 'other')",
            name="language",
        ),
        CheckConstraint(
            "facts_status IN ('pending', 'ready', 'review', 'error')",
            name="facts_status",
        ),
        CheckConstraint(
            "(status = 'active' AND unavailable_at IS NULL) OR (status = 'unavailable' AND unavailable_at IS NOT NULL)",
            name="availability_timestamp",
        ),
        Index("ix_canonical_jobs_status_posted", "status", "posted_at"),
        Index("ix_canonical_jobs_normalized_identity", "normalized_company", "normalized_title"),
    )

    facts_model_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_models.id", ondelete="SET NULL")
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_company: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    application_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    language: Mapped[str | None] = mapped_column(String(10))
    employment_types: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    work_modes: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    restrictions: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    facts: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    evidence: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    facts_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    unavailable_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )


class JobLocation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_locations"
    __table_args__ = (
        CheckConstraint(
            "workplace_type IN ('onsite', 'hybrid', 'remote', 'unknown')",
            name="workplace_type",
        ),
        CheckConstraint(
            "remote_scope IS NULL OR remote_scope IN ('eu_eea_ch', 'country', 'restricted', 'global', 'unknown')",
            name="remote_scope",
        ),
        CheckConstraint(
            "latitude IS NULL OR latitude BETWEEN -90 AND 90",
            name="latitude",
        ),
        CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180",
            name="longitude",
        ),
        CheckConstraint(
            "(latitude IS NULL) = (longitude IS NULL)",
            name="coordinates_pair",
        ),
        CheckConstraint(
            "resolution_confidence IS NULL OR resolution_confidence BETWEEN 0 AND 1",
            name="resolution_confidence",
        ),
        Index("ix_job_locations_country_city", "country_code", "city"),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("canonical_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str | None] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(120))
    country_code: Mapped[str | None] = mapped_column(String(2))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    workplace_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unknown", server_default="unknown"
    )
    remote_scope: Mapped[str | None] = mapped_column(String(20))
    resolution_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    resolution_source: Mapped[str | None] = mapped_column(String(50))


class PoolJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "pool_jobs"
    __table_args__ = (
        CheckConstraint("status IN ('candidate', 'active', 'rejected')", name="status"),
        CheckConstraint(
            "routing_score IS NULL OR routing_score BETWEEN 0 AND 1",
            name="routing_score",
        ),
        CheckConstraint(
            "linked_by IN ('rules', 'embedding', 'ai', 'admin')",
            name="linked_by",
        ),
        UniqueConstraint("pool_id", "job_id", name="uq_pool_jobs_pool_job"),
        Index("ix_pool_jobs_pool_status", "pool_id", "status"),
    )

    pool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("role_pools.id", ondelete="CASCADE"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_jobs.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="candidate", server_default="candidate"
    )
    routing_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    linked_by: Mapped[str] = mapped_column(String(30), nullable=False)
