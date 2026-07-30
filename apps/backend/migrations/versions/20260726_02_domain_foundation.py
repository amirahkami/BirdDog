"""Replace the provisional feature tables with the v1 domain foundation.

Revision ID: 20260726_02
Revises: 20260723_01
Create Date: 2026-07-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260726_02"
down_revision: str | None = "20260723_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def _id() -> sa.Column:
    return sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False)


def _json_object() -> sa.TextClause:
    return sa.text("'{}'::jsonb")


def _json_array() -> sa.TextClause:
    return sa.text("'[]'::jsonb")


def upgrade() -> None:
    # These tables were explicitly provisional and contained no feature data when replaced.
    op.drop_table("cover_letters")
    op.drop_index("ix_matches_niche_score", table_name="matches")
    op.drop_table("matches")
    op.drop_index("ix_jobs_status_posted_at", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_niches_user_active", table_name="niches")
    op.drop_table("niches")
    op.drop_table("cvs")
    op.drop_table("companies")

    op.create_table(
        "ai_providers",
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("adapter_type", sa.String(length=30), nullable=False),
        sa.Column("base_url", sa.String(length=1000), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("health_status", sa.String(length=20), server_default="unknown", nullable=False),
        sa.Column("last_health_at", sa.DateTime(timezone=True), nullable=True),
        _id(),
        *_timestamps(),
        sa.CheckConstraint(
            "adapter_type IN ('openwebui', 'openai_compatible')",
            name=op.f("ck_ai_providers_adapter_type"),
        ),
        sa.CheckConstraint(
            "health_status IN ('unknown', 'healthy', 'degraded', 'offline')",
            name=op.f("ck_ai_providers_health_status"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_providers")),
        sa.UniqueConstraint("code", name=op.f("uq_ai_providers_code")),
    )

    op.create_table(
        "ai_models",
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_model_id", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("supported_tasks", postgresql.JSONB(), server_default=_json_array(), nullable=False),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=True),
        sa.Column("max_concurrency", sa.Integer(), server_default="1", nullable=False),
        sa.Column("benchmark_version", sa.String(length=100), nullable=True),
        sa.Column("benchmark_status", sa.String(length=20), server_default="untested", nullable=False),
        sa.Column("benchmark_metrics", postgresql.JSONB(), server_default=_json_object(), nullable=False),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        _id(),
        *_timestamps(),
        sa.CheckConstraint(
            "benchmark_status IN ('untested', 'approved', 'rejected')",
            name=op.f("ck_ai_models_benchmark_status"),
        ),
        sa.CheckConstraint("max_concurrency >= 1", name=op.f("ck_ai_models_max_concurrency")),
        sa.CheckConstraint(
            "embedding_dimensions IS NULL OR embedding_dimensions >= 1",
            name=op.f("ck_ai_models_embedding_dimensions"),
        ),
        sa.ForeignKeyConstraint(
            ["provider_id"], ["ai_providers.id"],
            name=op.f("fk_ai_models_provider_id_ai_providers"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_models")),
        sa.UniqueConstraint("provider_id", "external_model_id", name="uq_ai_models_provider_external"),
    )

    op.create_table(
        "ai_routes",
        sa.Column("task", sa.String(length=50), nullable=False),
        sa.Column("primary_model_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fallback_model_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        _id(),
        *_timestamps(),
        sa.CheckConstraint(
            "task IN ('candidate_facts', 'job_facts', 'embeddings', 'role_candidates')",
            name=op.f("ck_ai_routes_task"),
        ),
        sa.CheckConstraint(
            "fallback_model_id IS NULL OR fallback_model_id <> primary_model_id",
            name=op.f("ck_ai_routes_different_fallback"),
        ),
        sa.ForeignKeyConstraint(
            ["fallback_model_id"], ["ai_models.id"],
            name=op.f("fk_ai_routes_fallback_model_id_ai_models"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["primary_model_id"], ["ai_models.id"],
            name=op.f("fk_ai_routes_primary_model_id_ai_models"), ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_routes")),
        sa.UniqueConstraint("task", name=op.f("uq_ai_routes_task")),
    )

    op.create_table(
        "user_profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("desired_role_text", sa.String(length=255), nullable=True),
        sa.Column("home_label", sa.String(length=255), nullable=True),
        sa.Column("home_city", sa.String(length=120), nullable=True),
        sa.Column("home_country_code", sa.String(length=2), nullable=True),
        sa.Column("home_latitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("home_longitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("travel_radius_km", sa.SmallInteger(), nullable=True),
        sa.Column("accepts_onsite", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("accepts_hybrid", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("accepts_remote", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("accepts_full_time", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("accepts_part_time", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("onboarding_status", sa.String(length=20), server_default="incomplete", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        _id(),
        *_timestamps(),
        sa.CheckConstraint(
            "onboarding_status IN ('incomplete', 'processing', 'ready', 'error')",
            name=op.f("ck_user_profiles_onboarding_status"),
        ),
        sa.CheckConstraint(
            "home_latitude IS NULL OR home_latitude BETWEEN -90 AND 90",
            name=op.f("ck_user_profiles_home_latitude"),
        ),
        sa.CheckConstraint(
            "home_longitude IS NULL OR home_longitude BETWEEN -180 AND 180",
            name=op.f("ck_user_profiles_home_longitude"),
        ),
        sa.CheckConstraint(
            "(home_latitude IS NULL) = (home_longitude IS NULL)",
            name=op.f("ck_user_profiles_home_coordinates_pair"),
        ),
        sa.CheckConstraint(
            "travel_radius_km IS NULL OR travel_radius_km >= 0",
            name=op.f("ck_user_profiles_travel_radius_km"),
        ),
        sa.CheckConstraint(
            "onboarding_status <> 'ready' OR (accepts_onsite OR accepts_hybrid OR accepts_remote)",
            name=op.f("ck_user_profiles_ready_work_mode"),
        ),
        sa.CheckConstraint(
            "onboarding_status <> 'ready' OR (accepts_full_time OR accepts_part_time)",
            name=op.f("ck_user_profiles_ready_employment_type"),
        ),
        sa.CheckConstraint(
            "onboarding_status <> 'ready' OR (desired_role_text IS NOT NULL AND btrim(desired_role_text) <> '' AND home_country_code IS NOT NULL AND home_latitude IS NOT NULL)",
            name=op.f("ck_user_profiles_ready_identity"),
        ),
        sa.CheckConstraint(
            "onboarding_status <> 'ready' OR NOT (accepts_onsite OR accepts_hybrid) OR travel_radius_km IS NOT NULL",
            name=op.f("ck_user_profiles_ready_radius"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_user_profiles_user_id_users"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_profiles")),
        sa.UniqueConstraint("user_id", name=op.f("uq_user_profiles_user_id")),
    )

    op.create_table(
        "cv_documents",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("facts_model_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("detected_language", sa.String(length=10), nullable=True),
        sa.Column("facts_schema_version", sa.String(length=50), nullable=True),
        sa.Column("facts", postgresql.JSONB(), server_default=_json_object(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), server_default=_json_object(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("is_current", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        _id(),
        *_timestamps(),
        sa.CheckConstraint("byte_size BETWEEN 1 AND 26214400", name=op.f("ck_cv_documents_byte_size")),
        sa.CheckConstraint(
            "page_count IS NULL OR page_count BETWEEN 1 AND 50",
            name=op.f("ck_cv_documents_page_count"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'extracting', 'ready', 'error')",
            name=op.f("ck_cv_documents_status"),
        ),
        sa.CheckConstraint(
            "detected_language IS NULL OR detected_language IN ('de', 'en', 'other')",
            name=op.f("ck_cv_documents_detected_language"),
        ),
        sa.CheckConstraint("content_type = 'application/pdf'", name=op.f("ck_cv_documents_content_type")),
        sa.CheckConstraint("char_length(sha256) = 64", name=op.f("ck_cv_documents_sha256")),
        sa.ForeignKeyConstraint(
            ["facts_model_id"], ["ai_models.id"],
            name=op.f("fk_cv_documents_facts_model_id_ai_models"), ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_cv_documents_user_id_users"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cv_documents")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_cv_documents_storage_key")),
    )
    op.create_index(
        "uq_cv_documents_current_user", "cv_documents", ["user_id"], unique=True,
        postgresql_where=sa.text("is_current"),
    )

    op.create_table(
        "role_concepts",
        sa.Column("preferred_label", sa.String(length=255), nullable=False),
        sa.Column("normalized_label", sa.String(length=255), nullable=False),
        sa.Column("taxonomy", sa.String(length=20), server_default="internal", nullable=False),
        sa.Column("taxonomy_version", sa.String(length=50), nullable=True),
        sa.Column("esco_uri", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="proposed", nullable=False),
        _id(),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('proposed', 'approved', 'disabled')",
            name=op.f("ck_role_concepts_status"),
        ),
        sa.CheckConstraint(
            "taxonomy IN ('internal', 'esco')",
            name=op.f("ck_role_concepts_taxonomy"),
        ),
        sa.CheckConstraint(
            "taxonomy = 'internal' OR (taxonomy_version IS NOT NULL AND esco_uri IS NOT NULL)",
            name=op.f("ck_role_concepts_versioned_external_taxonomy"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role_concepts")),
        sa.UniqueConstraint("esco_uri", name=op.f("uq_role_concepts_esco_uri")),
        sa.UniqueConstraint("normalized_label", name=op.f("uq_role_concepts_normalized_label")),
    )

    op.create_table(
        "role_aliases",
        sa.Column("role_concept_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.Column("normalized_alias", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        _id(),
        *_timestamps(),
        sa.CheckConstraint("language IN ('de', 'en', 'other')", name=op.f("ck_role_aliases_language")),
        sa.CheckConstraint("source IN ('user', 'esco', 'admin', 'ai')", name=op.f("ck_role_aliases_source")),
        sa.ForeignKeyConstraint(
            ["role_concept_id"], ["role_concepts.id"],
            name=op.f("fk_role_aliases_role_concept_id_role_concepts"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role_aliases")),
        sa.UniqueConstraint(
            "role_concept_id", "language", "normalized_alias",
            name="uq_role_aliases_role_language_alias",
        ),
    )
    op.create_index("ix_role_aliases_normalized_alias", "role_aliases", ["normalized_alias"])

    op.create_table(
        "role_pools",
        sa.Column("primary_role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="proposed", nullable=False),
        sa.Column("refresh_interval_minutes", sa.Integer(), server_default="1440", nullable=False),
        sa.Column("strike_limit", sa.Integer(), server_default="2", nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        _id(),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('proposed', 'building', 'active', 'paused', 'dropped', 'error')",
            name=op.f("ck_role_pools_status"),
        ),
        sa.CheckConstraint(
            "refresh_interval_minutes BETWEEN 60 AND 10080",
            name=op.f("ck_role_pools_refresh_interval_minutes"),
        ),
        sa.CheckConstraint("strike_limit BETWEEN 1 AND 5", name=op.f("ck_role_pools_strike_limit")),
        sa.ForeignKeyConstraint(
            ["approved_by_user_id"], ["users.id"],
            name=op.f("fk_role_pools_approved_by_user_id_users"), ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["primary_role_id"], ["role_concepts.id"],
            name=op.f("fk_role_pools_primary_role_id_role_concepts"), ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role_pools")),
        sa.UniqueConstraint("primary_role_id", name=op.f("uq_role_pools_primary_role_id")),
        sa.UniqueConstraint("slug", name=op.f("uq_role_pools_slug")),
    )

    op.create_table(
        "role_pool_relations",
        sa.Column("left_pool_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("right_pool_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("relation_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="proposed", nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        _id(),
        *_timestamps(),
        sa.CheckConstraint("left_pool_id <> right_pool_id", name=op.f("ck_role_pool_relations_different_pools")),
        sa.CheckConstraint("left_pool_id < right_pool_id", name=op.f("ck_role_pool_relations_canonical_pair_order")),
        sa.CheckConstraint(
            "relation_type IN ('related', 'overlapping')",
            name=op.f("ck_role_pool_relations_relation_type"),
        ),
        sa.CheckConstraint(
            "status IN ('proposed', 'approved', 'rejected')",
            name=op.f("ck_role_pool_relations_status"),
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_user_id"], ["users.id"],
            name=op.f("fk_role_pool_relations_approved_by_user_id_users"), ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["left_pool_id"], ["role_pools.id"],
            name=op.f("fk_role_pool_relations_left_pool_id_role_pools"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["right_pool_id"], ["role_pools.id"],
            name=op.f("fk_role_pool_relations_right_pool_id_role_pools"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role_pool_relations")),
        sa.UniqueConstraint("left_pool_id", "right_pool_id", name="uq_role_pool_relations_pair"),
    )

    op.create_table(
        "user_pool_memberships",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pool_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("desired_role_text", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="waiting", nullable=False),
        _id(),
        *_timestamps(),
        sa.CheckConstraint("status IN ('waiting', 'active', 'paused')", name=op.f("ck_user_pool_memberships_status")),
        sa.ForeignKeyConstraint(
            ["pool_id"], ["role_pools.id"],
            name=op.f("fk_user_pool_memberships_pool_id_role_pools"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name=op.f("fk_user_pool_memberships_user_id_users"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_pool_memberships")),
        sa.UniqueConstraint("user_id", "pool_id", name="uq_user_pool_memberships_user_pool"),
    )
    op.create_index(
        "ix_user_pool_memberships_pool_status", "user_pool_memberships", ["pool_id", "status"]
    )

    op.create_table(
        "canonical_jobs",
        sa.Column("facts_model_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_company", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("normalized_title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("application_url", sa.String(length=2000), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("employment_types", postgresql.JSONB(), server_default=_json_array(), nullable=False),
        sa.Column("work_modes", postgresql.JSONB(), server_default=_json_array(), nullable=False),
        sa.Column("restrictions", postgresql.JSONB(), server_default=_json_object(), nullable=False),
        sa.Column("facts", postgresql.JSONB(), server_default=_json_object(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), server_default=_json_object(), nullable=False),
        sa.Column("facts_status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("unavailable_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        _id(),
        *_timestamps(),
        sa.CheckConstraint("status IN ('active', 'unavailable')", name=op.f("ck_canonical_jobs_status")),
        sa.CheckConstraint(
            "language IS NULL OR language IN ('de', 'en', 'other')",
            name=op.f("ck_canonical_jobs_language"),
        ),
        sa.CheckConstraint(
            "facts_status IN ('pending', 'ready', 'review', 'error')",
            name=op.f("ck_canonical_jobs_facts_status"),
        ),
        sa.CheckConstraint(
            "(status = 'active' AND unavailable_at IS NULL) OR (status = 'unavailable' AND unavailable_at IS NOT NULL)",
            name=op.f("ck_canonical_jobs_availability_timestamp"),
        ),
        sa.ForeignKeyConstraint(
            ["facts_model_id"], ["ai_models.id"],
            name=op.f("fk_canonical_jobs_facts_model_id_ai_models"), ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_canonical_jobs")),
    )
    op.create_index("ix_canonical_jobs_status_posted", "canonical_jobs", ["status", "posted_at"])
    op.create_index(
        "ix_canonical_jobs_normalized_identity", "canonical_jobs", ["normalized_company", "normalized_title"]
    )

    op.create_table(
        "job_locations",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(length=500), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("workplace_type", sa.String(length=20), server_default="unknown", nullable=False),
        sa.Column("remote_scope", sa.String(length=20), nullable=True),
        sa.Column("resolution_confidence", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("resolution_source", sa.String(length=50), nullable=True),
        _id(),
        *_timestamps(),
        sa.CheckConstraint(
            "workplace_type IN ('onsite', 'hybrid', 'remote', 'unknown')",
            name=op.f("ck_job_locations_workplace_type"),
        ),
        sa.CheckConstraint(
            "remote_scope IS NULL OR remote_scope IN ('eu_eea_ch', 'country', 'restricted', 'global', 'unknown')",
            name=op.f("ck_job_locations_remote_scope"),
        ),
        sa.CheckConstraint(
            "latitude IS NULL OR latitude BETWEEN -90 AND 90",
            name=op.f("ck_job_locations_latitude"),
        ),
        sa.CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180",
            name=op.f("ck_job_locations_longitude"),
        ),
        sa.CheckConstraint(
            "(latitude IS NULL) = (longitude IS NULL)",
            name=op.f("ck_job_locations_coordinates_pair"),
        ),
        sa.CheckConstraint(
            "resolution_confidence IS NULL OR resolution_confidence BETWEEN 0 AND 1",
            name=op.f("ck_job_locations_resolution_confidence"),
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["canonical_jobs.id"],
            name=op.f("fk_job_locations_job_id_canonical_jobs"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_locations")),
    )
    op.create_index("ix_job_locations_country_city", "job_locations", ["country_code", "city"])

    op.create_table(
        "source_adapters",
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("layer", sa.String(length=20), nullable=False),
        sa.Column("terms_status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("attribution_required", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("minimum_poll_minutes", sa.Integer(), server_default="60", nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("configuration", postgresql.JSONB(), server_default=_json_object(), nullable=False),
        _id(),
        *_timestamps(),
        sa.CheckConstraint("layer IN ('primary', 'secondary', 'discovery')", name=op.f("ck_source_adapters_layer")),
        sa.CheckConstraint(
            "terms_status IN ('approved', 'pending', 'blocked')",
            name=op.f("ck_source_adapters_terms_status"),
        ),
        sa.CheckConstraint("minimum_poll_minutes >= 1", name=op.f("ck_source_adapters_minimum_poll_minutes")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_adapters")),
        sa.UniqueConstraint("code", name=op.f("uq_source_adapters_code")),
    )

    op.create_table(
        "source_boards",
        sa.Column("adapter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_key", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("careers_url", sa.String(length=2000), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("etag", sa.String(length=500), nullable=True),
        sa.Column("last_modified", sa.String(length=255), nullable=True),
        sa.Column("body_hash", sa.String(length=64), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), server_default="0", nullable=False),
        _id(),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('active', 'silent', 'stale', 'paused', 'blocked')",
            name=op.f("ck_source_boards_status"),
        ),
        sa.CheckConstraint("consecutive_failures >= 0", name=op.f("ck_source_boards_consecutive_failures")),
        sa.ForeignKeyConstraint(
            ["adapter_id"], ["source_adapters.id"],
            name=op.f("fk_source_boards_adapter_id_source_adapters"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_boards")),
        sa.UniqueConstraint("adapter_id", "external_key", name="uq_source_boards_adapter_key"),
    )
    op.create_index("ix_source_boards_adapter_status", "source_boards", ["adapter_id", "status"])

    op.create_table(
        "source_runs",
        sa.Column("board_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("run_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("jobs_seen", sa.Integer(), server_default="0", nullable=False),
        sa.Column("jobs_changed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        _id(),
        *_timestamps(),
        sa.CheckConstraint("run_type IN ('discovery', 'listing', 'detail')", name=op.f("ck_source_runs_run_type")),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'unchanged', 'failed', 'paused')",
            name=op.f("ck_source_runs_status"),
        ),
        sa.CheckConstraint("jobs_seen >= 0 AND jobs_changed >= 0", name=op.f("ck_source_runs_job_counts")),
        sa.ForeignKeyConstraint(
            ["board_id"], ["source_boards.id"],
            name=op.f("fk_source_runs_board_id_source_boards"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_runs")),
    )
    op.create_index("ix_source_runs_board_started", "source_runs", ["board_id", "started_at"])

    op.create_table(
        "source_job_observations",
        sa.Column("board_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("canonical_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("facts_model_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("external_id", sa.String(length=500), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("location_text", sa.String(length=1000), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(length=2000), nullable=False),
        sa.Column("application_url", sa.String(length=2000), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("source_workplace_type", sa.String(length=30), nullable=True),
        sa.Column("source_employment_type", sa.String(length=50), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(), server_default=_json_object(), nullable=False),
        sa.Column("facts", postgresql.JSONB(), server_default=_json_object(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), server_default=_json_object(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("missing_strikes", sa.Integer(), server_default="0", nullable=False),
        _id(),
        *_timestamps(),
        sa.CheckConstraint("status IN ('active', 'unavailable')", name=op.f("ck_source_job_observations_status")),
        sa.CheckConstraint("missing_strikes BETWEEN 0 AND 5", name=op.f("ck_source_job_observations_missing_strikes")),
        sa.CheckConstraint(
            "language IS NULL OR language IN ('de', 'en', 'other')",
            name=op.f("ck_source_job_observations_language"),
        ),
        sa.ForeignKeyConstraint(
            ["board_id"], ["source_boards.id"],
            name=op.f("fk_source_job_observations_board_id_source_boards"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["canonical_job_id"], ["canonical_jobs.id"],
            name=op.f("fk_source_job_observations_canonical_job_id_canonical_jobs"), ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["facts_model_id"], ["ai_models.id"],
            name=op.f("fk_source_job_observations_facts_model_id_ai_models"), ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_job_observations")),
        sa.UniqueConstraint("board_id", "external_id", name="uq_source_job_observations_identity"),
    )
    op.create_index(
        "ix_source_job_observations_canonical", "source_job_observations", ["canonical_job_id"]
    )
    op.create_index(
        "ix_source_job_observations_board_status", "source_job_observations", ["board_id", "status"]
    )

    op.create_table(
        "pool_jobs",
        sa.Column("pool_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="candidate", nullable=False),
        sa.Column("routing_score", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("linked_by", sa.String(length=30), nullable=False),
        _id(),
        *_timestamps(),
        sa.CheckConstraint("status IN ('candidate', 'active', 'rejected')", name=op.f("ck_pool_jobs_status")),
        sa.CheckConstraint(
            "routing_score IS NULL OR routing_score BETWEEN 0 AND 1",
            name=op.f("ck_pool_jobs_routing_score"),
        ),
        sa.CheckConstraint(
            "linked_by IN ('rules', 'embedding', 'ai', 'admin')",
            name=op.f("ck_pool_jobs_linked_by"),
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["canonical_jobs.id"],
            name=op.f("fk_pool_jobs_job_id_canonical_jobs"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["pool_id"], ["role_pools.id"],
            name=op.f("fk_pool_jobs_pool_id_role_pools"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pool_jobs")),
        sa.UniqueConstraint("pool_id", "job_id", name="uq_pool_jobs_pool_job"),
    )
    op.create_index("ix_pool_jobs_pool_status", "pool_jobs", ["pool_id", "status"])

    op.create_table(
        "work_items",
        sa.Column("kind", sa.String(length=100), nullable=False),
        sa.Column("idempotency_key", sa.String(length=500), nullable=False),
        sa.Column("subject_type", sa.String(length=100), nullable=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(), server_default=_json_object(), nullable=False),
        sa.Column("priority", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="queued", nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(length=255), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        _id(),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'completed', 'failed', 'dead')",
            name=op.f("ck_work_items_status"),
        ),
        sa.CheckConstraint("attempts >= 0 AND max_attempts >= 1", name=op.f("ck_work_items_attempts")),
        sa.CheckConstraint("priority BETWEEN -100 AND 100", name=op.f("ck_work_items_priority")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_work_items")),
        sa.UniqueConstraint("idempotency_key", name=op.f("uq_work_items_idempotency_key")),
    )
    op.create_index("ix_work_items_claim", "work_items", ["status", "available_at", "priority"])

    op.create_table(
        "user_matches",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pool_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("tier", sa.String(length=20), nullable=False),
        sa.Column("eligibility", sa.String(length=20), nullable=False),
        sa.Column("reasons", postgresql.JSONB(), server_default=_json_array(), nullable=False),
        sa.Column("missing_facts", postgresql.JSONB(), server_default=_json_array(), nullable=False),
        sa.Column("algorithm_version", sa.String(length=50), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        _id(),
        *_timestamps(),
        sa.CheckConstraint("score BETWEEN 0 AND 100", name=op.f("ck_user_matches_score")),
        sa.CheckConstraint(
            "tier IN ('strong', 'good', 'stretch', 'blocked', 'review')",
            name=op.f("ck_user_matches_tier"),
        ),
        sa.CheckConstraint(
            "eligibility IN ('eligible', 'blocked', 'review')",
            name=op.f("ck_user_matches_eligibility"),
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["canonical_jobs.id"],
            name=op.f("fk_user_matches_job_id_canonical_jobs"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["pool_id"], ["role_pools.id"],
            name=op.f("fk_user_matches_pool_id_role_pools"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name=op.f("fk_user_matches_user_id_users"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_matches")),
        sa.UniqueConstraint("user_id", "job_id", name="uq_user_matches_user_job"),
    )
    op.create_index("ix_user_matches_user_score", "user_matches", ["user_id", "score"])

    op.create_table(
        "user_job_actions",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("preference", sa.String(length=20), nullable=True),
        sa.Column("last_application_opened_at", sa.DateTime(timezone=True), nullable=True),
        _id(),
        *_timestamps(),
        sa.CheckConstraint(
            "preference IS NULL OR preference IN ('liked', 'disliked')",
            name=op.f("ck_user_job_actions_preference"),
        ),
        sa.CheckConstraint(
            "preference IS NOT NULL OR last_application_opened_at IS NOT NULL",
            name=op.f("ck_user_job_actions_has_action"),
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["canonical_jobs.id"],
            name=op.f("fk_user_job_actions_job_id_canonical_jobs"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name=op.f("fk_user_job_actions_user_id_users"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_job_actions")),
        sa.UniqueConstraint("user_id", "job_id", name="uq_user_job_actions_user_job"),
    )
    op.create_index(
        "ix_user_job_actions_user_preference", "user_job_actions", ["user_id", "preference"]
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_user_job_actions_user_preference")
    op.execute("DROP INDEX IF EXISTS ix_user_job_actions_user_action")
    op.drop_table("user_job_actions")
    op.drop_index("ix_user_matches_user_score", table_name="user_matches")
    op.drop_table("user_matches")
    op.drop_index("ix_work_items_claim", table_name="work_items")
    op.drop_table("work_items")
    op.drop_index("ix_pool_jobs_pool_status", table_name="pool_jobs")
    op.drop_table("pool_jobs")
    op.drop_index("ix_source_job_observations_board_status", table_name="source_job_observations")
    op.drop_index("ix_source_job_observations_canonical", table_name="source_job_observations")
    op.drop_table("source_job_observations")
    op.drop_index("ix_source_runs_board_started", table_name="source_runs")
    op.drop_table("source_runs")
    op.drop_index("ix_source_boards_adapter_status", table_name="source_boards")
    op.drop_table("source_boards")
    op.drop_table("source_adapters")
    op.drop_index("ix_job_locations_country_city", table_name="job_locations")
    op.drop_table("job_locations")
    op.drop_index("ix_canonical_jobs_normalized_identity", table_name="canonical_jobs")
    op.drop_index("ix_canonical_jobs_status_posted", table_name="canonical_jobs")
    op.drop_table("canonical_jobs")
    op.drop_index("ix_user_pool_memberships_pool_status", table_name="user_pool_memberships")
    op.drop_table("user_pool_memberships")
    op.drop_table("role_pool_relations")
    op.drop_table("role_pools")
    op.drop_index("ix_role_aliases_normalized_alias", table_name="role_aliases")
    op.drop_table("role_aliases")
    op.drop_table("role_concepts")
    op.drop_index("uq_cv_documents_current_user", table_name="cv_documents")
    op.drop_table("cv_documents")
    op.drop_table("user_profiles")
    op.drop_table("ai_routes")
    op.drop_table("ai_models")
    op.drop_table("ai_providers")

    _restore_provisional_tables()


def _restore_provisional_tables() -> None:
    op.create_table(
        "companies",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("ats_type", sa.String(length=50), nullable=False),
        sa.Column("ats_token", sa.String(length=255), nullable=False),
        sa.Column("careers_url", sa.String(length=1000), nullable=True),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
        _id(),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_companies")),
        sa.UniqueConstraint("ats_type", "ats_token", name="uq_companies_ats_identity"),
        sa.UniqueConstraint("slug", name=op.f("uq_companies_slug")),
    )
    op.create_table(
        "cvs",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("parsed_text", sa.Text(), nullable=True),
        sa.Column("detected_level", sa.String(length=50), nullable=True),
        sa.Column("parse_status", sa.String(length=20), server_default="pending", nullable=False),
        _id(),
        *_timestamps(),
        sa.CheckConstraint(
            "parse_status IN ('pending', 'parsed', 'error')", name=op.f("ck_cvs_parse_status")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_cvs_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cvs")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_cvs_storage_key")),
        sa.UniqueConstraint("user_id", name=op.f("uq_cvs_user_id")),
    )
    op.create_table(
        "niches",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=255), nullable=False),
        sa.Column("place_mode", sa.String(length=20), nullable=False),
        sa.Column("location_city", sa.String(length=120), nullable=True),
        sa.Column("location_region", sa.String(length=120), nullable=True),
        sa.Column("target_level", sa.String(length=50), nullable=True),
        sa.Column("keywords", postgresql.JSONB(), server_default=_json_array(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        _id(),
        *_timestamps(),
        sa.CheckConstraint(
            "place_mode IN ('on_site', 'remote_de', 'remote_eu')",
            name=op.f("ck_niches_place_mode"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_niches_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_niches")),
    )
    op.create_index("ix_niches_user_active", "niches", ["user_id", "is_active"])
    op.create_table(
        "jobs",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("source_layer", sa.SmallInteger(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("location", sa.String(length=500), nullable=False),
        sa.Column("remote_type", sa.String(length=30), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("url", sa.String(length=2000), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("dedup_key", sa.String(length=1000), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(), server_default=_json_object(), nullable=False),
        _id(),
        *_timestamps(),
        sa.CheckConstraint("source_layer BETWEEN 1 AND 4", name=op.f("ck_jobs_source_layer")),
        sa.CheckConstraint(
            "language IS NULL OR language IN ('de', 'en', 'other')",
            name=op.f("ck_jobs_language"),
        ),
        sa.CheckConstraint(
            "remote_type IS NULL OR remote_type IN ('on_site', 'hybrid', 'remote_de', 'remote_eu', 'remote_global')",
            name=op.f("ck_jobs_remote_type"),
        ),
        sa.CheckConstraint("status IN ('active', 'closed')", name=op.f("ck_jobs_status")),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"],
            name=op.f("fk_jobs_company_id_companies"), ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
        sa.UniqueConstraint("dedup_key", name=op.f("uq_jobs_dedup_key")),
        sa.UniqueConstraint("source", "source_id", name="uq_jobs_source_identity"),
    )
    op.create_index("ix_jobs_status_posted_at", "jobs", ["status", "posted_at"])
    op.create_table(
        "matches",
        sa.Column("niche_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fit_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("verdict", sa.String(length=20), nullable=False),
        sa.Column("why", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("is_seen", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_applied", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("matched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        _id(),
        *_timestamps(),
        sa.CheckConstraint("fit_score BETWEEN 0 AND 100", name=op.f("ck_matches_fit_score")),
        sa.CheckConstraint("verdict IN ('strong', 'possible', 'reject')", name=op.f("ck_matches_verdict")),
        sa.ForeignKeyConstraint(
            ["job_id"], ["jobs.id"], name=op.f("fk_matches_job_id_jobs"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["niche_id"], ["niches.id"], name=op.f("fk_matches_niche_id_niches"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_matches")),
        sa.UniqueConstraint("niche_id", "job_id", name="uq_matches_niche_job"),
    )
    op.create_index("ix_matches_niche_score", "matches", ["niche_id", "fit_score"])
    op.create_table(
        "cover_letters",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=2), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        _id(),
        *_timestamps(),
        sa.CheckConstraint("language IN ('en', 'de')", name=op.f("ck_cover_letters_language")),
        sa.ForeignKeyConstraint(
            ["job_id"], ["jobs.id"], name=op.f("fk_cover_letters_job_id_jobs"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_cover_letters_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cover_letters")),
        sa.UniqueConstraint("user_id", "job_id", name="uq_cover_letters_user_job"),
    )
