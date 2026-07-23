from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Niche(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "niches"
    __table_args__ = (
        CheckConstraint(
            "place_mode IN ('on_site', 'remote_de', 'remote_eu')",
            name="place_mode",
        ),
        Index("ix_niches_user_active", "user_id", "is_active"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    place_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    location_city: Mapped[str | None] = mapped_column(String(120))
    location_region: Mapped[str | None] = mapped_column(String(120))
    target_level: Mapped[str | None] = mapped_column(String(50))
    keywords: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    user: Mapped[User] = relationship(back_populates="niches")
    matches: Mapped[list[Match]] = relationship(
        back_populates="niche",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


from app.db.models.match import Match
from app.db.models.user import User
