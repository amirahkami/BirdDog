import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SourceAdapter(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_adapters"
    __table_args__ = (
        CheckConstraint("layer IN ('primary', 'secondary', 'discovery')", name="layer"),
        CheckConstraint("terms_status IN ('approved', 'pending', 'blocked')", name="terms_status"),
        CheckConstraint("minimum_poll_minutes >= 1", name="minimum_poll_minutes"),
    )

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    layer: Mapped[str] = mapped_column(String(20), nullable=False)
    terms_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    attribution_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    minimum_poll_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60, server_default="60"
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )


class SourceBoard(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_boards"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'silent', 'stale', 'paused', 'blocked')", name="status"),
        CheckConstraint("consecutive_failures >= 0", name="consecutive_failures"),
        UniqueConstraint("adapter_id", "external_key", name="uq_source_boards_adapter_key"),
        Index("ix_source_boards_adapter_status", "adapter_id", "status"),
    )

    adapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_adapters.id", ondelete="CASCADE"), nullable=False
    )
    external_key: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    careers_url: Mapped[str | None] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    etag: Mapped[str | None] = mapped_column(String(500))
    last_modified: Mapped[str | None] = mapped_column(String(255))
    body_hash: Mapped[str | None] = mapped_column(String(64))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consecutive_failures: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )


class SourceRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_runs"
    __table_args__ = (
        CheckConstraint("run_type IN ('discovery', 'listing', 'detail')", name="run_type"),
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'unchanged', 'failed', 'paused')",
            name="status",
        ),
        CheckConstraint("jobs_seen >= 0 AND jobs_changed >= 0", name="job_counts"),
        Index("ix_source_runs_board_started", "board_id", "started_at"),
    )

    board_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_boards.id", ondelete="CASCADE")
    )
    run_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    http_status: Mapped[int | None] = mapped_column(Integer)
    jobs_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    jobs_changed: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text)


class SourceJobObservation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_job_observations"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'unavailable')", name="status"),
        CheckConstraint("missing_strikes BETWEEN 0 AND 5", name="missing_strikes"),
        CheckConstraint(
            "language IS NULL OR language IN ('de', 'en', 'other')",
            name="language",
        ),
        UniqueConstraint("board_id", "external_id", name="uq_source_job_observations_identity"),
        Index("ix_source_job_observations_canonical", "canonical_job_id"),
        Index("ix_source_job_observations_board_status", "board_id", "status"),
    )

    board_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_boards.id", ondelete="CASCADE"), nullable=False
    )
    canonical_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_jobs.id", ondelete="SET NULL")
    )
    facts_model_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_models.id", ondelete="SET NULL")
    )
    external_id: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_text: Mapped[str | None] = mapped_column(String(1000))
    description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    application_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    language: Mapped[str | None] = mapped_column(String(10))
    source_workplace_type: Mapped[str | None] = mapped_column(String(30))
    source_employment_type: Mapped[str | None] = mapped_column(String(50))
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    facts: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    evidence: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    missing_strikes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
