import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AIProvider(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_providers"
    __table_args__ = (
        CheckConstraint(
            "adapter_type IN ('openwebui', 'openai_compatible')",
            name="adapter_type",
        ),
        CheckConstraint(
            "health_status IN ('unknown', 'healthy', 'degraded', 'offline')",
            name="health_status",
        ),
    )

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    adapter_type: Mapped[str] = mapped_column(String(30), nullable=False)
    base_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    health_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unknown", server_default="unknown"
    )
    last_health_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AIModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_models"
    __table_args__ = (
        CheckConstraint(
            "benchmark_status IN ('untested', 'approved', 'rejected')",
            name="benchmark_status",
        ),
        CheckConstraint("max_concurrency >= 1", name="max_concurrency"),
        CheckConstraint(
            "embedding_dimensions IS NULL OR embedding_dimensions >= 1",
            name="embedding_dimensions",
        ),
        UniqueConstraint("provider_id", "external_model_id", name="uq_ai_models_provider_external"),
    )

    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False
    )
    external_model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    supported_tasks: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    embedding_dimensions: Mapped[int | None] = mapped_column(Integer)
    max_concurrency: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    benchmark_version: Mapped[str | None] = mapped_column(String(100))
    benchmark_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="untested", server_default="untested"
    )
    benchmark_metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AIRoute(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_routes"
    __table_args__ = (
        CheckConstraint(
            "task IN ('candidate_facts', 'job_facts', 'embeddings', 'role_candidates')",
            name="task",
        ),
        CheckConstraint(
            "fallback_model_id IS NULL OR fallback_model_id <> primary_model_id",
            name="different_fallback",
        ),
    )

    task: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    primary_model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_models.id", ondelete="RESTRICT"), nullable=False
    )
    fallback_model_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_models.id", ondelete="RESTRICT")
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
