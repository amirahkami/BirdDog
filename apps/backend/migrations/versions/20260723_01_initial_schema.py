"""Create the initial BirdDog schema.

Revision ID: 20260723_01
Revises:
Create Date: 2026-07-23
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260723_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamp_columns() -> list[sa.Column]:
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


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("keycloak_subject", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column(
            "preferred_language",
            sa.String(length=2),
            server_default="en",
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint(
            "preferred_language IN ('en', 'de')",
            name=op.f("ck_users_preferred_language"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
        sa.UniqueConstraint(
            "keycloak_subject",
            name=op.f("uq_users_keycloak_subject"),
        ),
    )

    op.create_table(
        "companies",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("ats_type", sa.String(length=50), nullable=False),
        sa.Column("ats_token", sa.String(length=255), nullable=False),
        sa.Column("careers_url", sa.String(length=1000), nullable=True),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_companies")),
        sa.UniqueConstraint(
            "ats_type",
            "ats_token",
            name="uq_companies_ats_identity",
        ),
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
        sa.Column(
            "parse_status",
            sa.String(length=20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint(
            "parse_status IN ('pending', 'parsed', 'error')",
            name=op.f("ck_cvs_parse_status"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_cvs_user_id_users"),
            ondelete="CASCADE",
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
        sa.Column(
            "keywords",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint(
            "place_mode IN ('on_site', 'remote_de', 'remote_eu')",
            name=op.f("ck_niches_place_mode"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_niches_user_id_users"),
            ondelete="CASCADE",
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
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="active",
            nullable=False,
        ),
        sa.Column("dedup_key", sa.String(length=1000), nullable=False),
        sa.Column(
            "raw_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint(
            "language IS NULL OR language IN ('de', 'en', 'other')",
            name=op.f("ck_jobs_language"),
        ),
        sa.CheckConstraint(
            "remote_type IS NULL OR remote_type IN ('on_site', 'hybrid', 'remote_de', 'remote_eu', 'remote_global')",
            name=op.f("ck_jobs_remote_type"),
        ),
        sa.CheckConstraint(
            "source_layer BETWEEN 1 AND 4",
            name=op.f("ck_jobs_source_layer"),
        ),
        sa.CheckConstraint(
            "status IN ('active', 'closed')",
            name=op.f("ck_jobs_status"),
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_jobs_company_id_companies"),
            ondelete="RESTRICT",
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
        sa.Column(
            "is_seen",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "is_applied",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "matched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint(
            "fit_score BETWEEN 0 AND 100",
            name=op.f("ck_matches_fit_score"),
        ),
        sa.CheckConstraint(
            "verdict IN ('strong', 'possible', 'reject')",
            name=op.f("ck_matches_verdict"),
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name=op.f("fk_matches_job_id_jobs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["niche_id"],
            ["niches.id"],
            name=op.f("fk_matches_niche_id_niches"),
            ondelete="CASCADE",
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
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint(
            "language IN ('en', 'de')",
            name=op.f("ck_cover_letters_language"),
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name=op.f("fk_cover_letters_job_id_jobs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_cover_letters_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cover_letters")),
        sa.UniqueConstraint(
            "user_id",
            "job_id",
            name="uq_cover_letters_user_job",
        ),
    )


def downgrade() -> None:
    op.drop_table("cover_letters")
    op.drop_index("ix_matches_niche_score", table_name="matches")
    op.drop_table("matches")
    op.drop_index("ix_jobs_status_posted_at", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_niches_user_active", table_name="niches")
    op.drop_table("niches")
    op.drop_table("cvs")
    op.drop_table("companies")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
