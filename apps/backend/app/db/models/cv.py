import uuid
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CVDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cv_documents"
    __table_args__ = (
        CheckConstraint(
            "byte_size BETWEEN 1 AND 26214400",
            name="byte_size",
        ),
        CheckConstraint(
            "page_count IS NULL OR page_count BETWEEN 1 AND 50",
            name="page_count",
        ),
        CheckConstraint(
            "extraction_status IN ('pending', 'processing', 'ready', 'error')",
            name="extraction_status",
        ),
        CheckConstraint(
            "extraction_method IS NULL OR extraction_method IN ('native', 'ocr', 'mixed')",
            name="extraction_method",
        ),
        CheckConstraint(
            "facts_status IN ('pending', 'queued', 'ready', 'review', 'error')",
            name="facts_status",
        ),
        CheckConstraint(
            "detected_language IS NULL OR detected_language IN ('de', 'en', 'other')",
            name="detected_language",
        ),
        CheckConstraint("content_type = 'application/pdf'", name="content_type"),
        CheckConstraint("char_length(sha256) = 64", name="sha256"),
        Index(
            "uq_cv_documents_current_user",
            "user_id",
            unique=True,
            postgresql_where=text("is_current"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    facts_model_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_models.id", ondelete="SET NULL"),
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(
        String(100), nullable=False, default="application/pdf"
    )
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    detected_language: Mapped[str | None] = mapped_column(String(10))
    facts_schema_version: Mapped[str | None] = mapped_column(String(50))
    facts: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    evidence: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    extraction_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    extraction_method: Mapped[str | None] = mapped_column(String(20))
    extraction_error_code: Mapped[str | None] = mapped_column(String(100))
    facts_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
