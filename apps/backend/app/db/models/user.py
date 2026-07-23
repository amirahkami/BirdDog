from __future__ import annotations

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "preferred_language IN ('en', 'de')",
            name="preferred_language",
        ),
    )

    keycloak_subject: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    preferred_language: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="en",
        server_default="en",
    )

    cv: Mapped[CV | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    niches: Mapped[list[Niche]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    cover_letters: Mapped[list[CoverLetter]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


from app.db.models.cover_letter import CoverLetter
from app.db.models.cv import CV
from app.db.models.niche import Niche
