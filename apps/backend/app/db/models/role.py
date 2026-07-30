import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RoleConcept(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "role_concepts"
    __table_args__ = (
        CheckConstraint("status IN ('proposed', 'approved', 'disabled')", name="status"),
        CheckConstraint("taxonomy IN ('internal', 'esco')", name="taxonomy"),
        CheckConstraint(
            "taxonomy = 'internal' OR (taxonomy_version IS NOT NULL AND esco_uri IS NOT NULL)",
            name="versioned_external_taxonomy",
        ),
    )

    preferred_label: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_label: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    taxonomy: Mapped[str] = mapped_column(
        String(20), nullable=False, default="internal", server_default="internal"
    )
    taxonomy_version: Mapped[str | None] = mapped_column(String(50))
    esco_uri: Mapped[str | None] = mapped_column(String(1000), unique=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="proposed", server_default="proposed"
    )


class RoleAlias(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "role_aliases"
    __table_args__ = (
        CheckConstraint("language IN ('de', 'en', 'other')", name="language"),
        CheckConstraint("source IN ('user', 'esco', 'admin', 'ai')", name="source"),
        UniqueConstraint(
            "role_concept_id", "language", "normalized_alias", name="uq_role_aliases_role_language_alias"
        ),
        Index("ix_role_aliases_normalized_alias", "normalized_alias"),
    )

    role_concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("role_concepts.id", ondelete="CASCADE"), nullable=False
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)


class RolePool(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "role_pools"
    __table_args__ = (
        CheckConstraint(
            "status IN ('proposed', 'building', 'active', 'paused', 'dropped', 'error')",
            name="status",
        ),
        CheckConstraint(
            "refresh_interval_minutes BETWEEN 60 AND 10080",
            name="refresh_interval_minutes",
        ),
        CheckConstraint("strike_limit BETWEEN 1 AND 5", name="strike_limit"),
    )

    primary_role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("role_concepts.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="proposed", server_default="proposed"
    )
    refresh_interval_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1440, server_default="1440"
    )
    strike_limit: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2, server_default="2"
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RolePoolRelation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "role_pool_relations"
    __table_args__ = (
        CheckConstraint("left_pool_id <> right_pool_id", name="different_pools"),
        CheckConstraint("left_pool_id < right_pool_id", name="canonical_pair_order"),
        CheckConstraint("relation_type IN ('related', 'overlapping')", name="relation_type"),
        CheckConstraint("status IN ('proposed', 'approved', 'rejected')", name="status"),
        UniqueConstraint("left_pool_id", "right_pool_id", name="uq_role_pool_relations_pair"),
    )

    left_pool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("role_pools.id", ondelete="CASCADE"), nullable=False
    )
    right_pool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("role_pools.id", ondelete="CASCADE"), nullable=False
    )
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    relation_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="proposed", server_default="proposed"
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserPoolMembership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_pool_memberships"
    __table_args__ = (
        CheckConstraint("status IN ('waiting', 'active', 'paused')", name="status"),
        UniqueConstraint("user_id", "pool_id", name="uq_user_pool_memberships_user_pool"),
        Index("ix_user_pool_memberships_pool_status", "pool_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    pool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("role_pools.id", ondelete="CASCADE"), nullable=False
    )
    desired_role_text: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="waiting", server_default="waiting"
    )
