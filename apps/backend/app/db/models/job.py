from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("source_layer BETWEEN 1 AND 4", name="source_layer"),
        CheckConstraint(
            "remote_type IS NULL OR remote_type IN ('on_site', 'hybrid', 'remote_de', 'remote_eu', 'remote_global')",
            name="remote_type",
        ),
        CheckConstraint(
            "language IS NULL OR language IN ('de', 'en', 'other')",
            name="language",
        ),
        CheckConstraint("status IN ('active', 'closed')", name="status"),
        UniqueConstraint("source", "source_id", name="uq_jobs_source_identity"),
        Index("ix_jobs_status_posted_at", "status", "posted_at"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_layer: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(500), nullable=False)
    remote_type: Mapped[str | None] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    language: Mapped[str | None] = mapped_column(String(10))
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )
    dedup_key: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    company: Mapped[Company] = relationship(back_populates="jobs")
    matches: Mapped[list[Match]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    cover_letters: Mapped[list[CoverLetter]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


from app.db.models.company import Company
from app.db.models.cover_letter import CoverLetter
from app.db.models.match import Match
