"""Add on-site/remote country lists to user profiles.

Revision ID: 20260830_04
Revises: 20260726_03
Create Date: 2026-08-30
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260830_04"
down_revision: str | None = "20260726_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column(
            "onsite_countries",
            postgresql.ARRAY(sa.String(length=2)),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )
    op.add_column(
        "user_profiles",
        sa.Column(
            "remote_countries",
            postgresql.ARRAY(sa.String(length=2)),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )
    # Home location is required for 'ready' only when on-site/hybrid is accepted.
    op.drop_constraint(op.f("ck_user_profiles_ready_identity"), "user_profiles", type_="check")
    op.create_check_constraint(
        op.f("ck_user_profiles_ready_identity"),
        "user_profiles",
        "onboarding_status <> 'ready' OR (desired_role_text IS NOT NULL AND btrim(desired_role_text) <> '' "
        "AND (NOT (accepts_onsite OR accepts_hybrid) OR (home_country_code IS NOT NULL AND home_latitude IS NOT NULL)))",
    )
    op.create_check_constraint(
        op.f("ck_user_profiles_ready_onsite_countries"),
        "user_profiles",
        "onboarding_status <> 'ready' OR NOT (accepts_onsite OR accepts_hybrid) "
        "OR array_length(onsite_countries, 1) >= 1",
    )
    op.create_check_constraint(
        op.f("ck_user_profiles_ready_remote_countries"),
        "user_profiles",
        "onboarding_status <> 'ready' OR NOT accepts_remote OR array_length(remote_countries, 1) >= 1",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_user_profiles_ready_remote_countries"), "user_profiles", type_="check")
    op.drop_constraint(op.f("ck_user_profiles_ready_onsite_countries"), "user_profiles", type_="check")
    op.drop_constraint(op.f("ck_user_profiles_ready_identity"), "user_profiles", type_="check")
    op.create_check_constraint(
        op.f("ck_user_profiles_ready_identity"),
        "user_profiles",
        "onboarding_status <> 'ready' OR (desired_role_text IS NOT NULL AND btrim(desired_role_text) <> '' "
        "AND home_country_code IS NOT NULL AND home_latitude IS NOT NULL)",
    )
    op.drop_column("user_profiles", "remote_countries")
    op.drop_column("user_profiles", "onsite_countries")
