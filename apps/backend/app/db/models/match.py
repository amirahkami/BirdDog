import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserMatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_matches"
    __table_args__ = (
        CheckConstraint("score BETWEEN 0 AND 100", name="score"),
        CheckConstraint(
            "tier IN ('strong', 'good', 'stretch', 'blocked', 'review')",
            name="tier",
        ),
        CheckConstraint(
            "eligibility IN ('eligible', 'blocked', 'review')",
            name="eligibility",
        ),
        UniqueConstraint("user_id", "job_id", name="uq_user_matches_user_job"),
        Index("ix_user_matches_user_score", "user_id", "score"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_jobs.id", ondelete="CASCADE"), nullable=False
    )
    pool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("role_pools.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    eligibility: Mapped[str] = mapped_column(String(20), nullable=False)
    reasons: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    missing_facts: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    algorithm_version: Mapped[str] = mapped_column(String(50), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class UserJobAction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_job_actions"
    __table_args__ = (
        CheckConstraint(
            "preference IS NULL OR preference IN ('liked', 'disliked')",
            name="preference",
        ),
        CheckConstraint(
            "preference IS NOT NULL OR last_application_opened_at IS NOT NULL",
            name="has_action",
        ),
        UniqueConstraint("user_id", "job_id", name="uq_user_job_actions_user_job"),
        Index("ix_user_job_actions_user_preference", "user_id", "preference"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_jobs.id", ondelete="CASCADE"), nullable=False
    )
    preference: Mapped[str | None] = mapped_column(String(20))
    last_application_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
