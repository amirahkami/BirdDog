"""Add explicit CV extraction and fact-processing state.

Revision ID: 20260726_03
Revises: 20260726_02
Create Date: 2026-07-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260726_03"
down_revision: str | None = "20260726_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(op.f("ck_cv_documents_status"), "cv_documents", type_="check")
    op.alter_column("cv_documents", "status", new_column_name="extraction_status")
    op.alter_column("cv_documents", "error_code", new_column_name="extraction_error_code")
    op.add_column("cv_documents", sa.Column("extraction_method", sa.String(length=20)))
    op.add_column(
        "cv_documents",
        sa.Column("facts_status", sa.String(length=20), server_default="pending", nullable=False),
    )
    op.execute(
        "UPDATE cv_documents SET extraction_status = 'processing' "
        "WHERE extraction_status = 'extracting'"
    )
    op.create_check_constraint(
        op.f("ck_cv_documents_extraction_status"),
        "cv_documents",
        "extraction_status IN ('pending', 'processing', 'ready', 'error')",
    )
    op.create_check_constraint(
        op.f("ck_cv_documents_extraction_method"),
        "cv_documents",
        "extraction_method IS NULL OR extraction_method IN ('native', 'ocr', 'mixed')",
    )
    op.create_check_constraint(
        op.f("ck_cv_documents_facts_status"),
        "cv_documents",
        "facts_status IN ('pending', 'queued', 'ready', 'review', 'error')",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_cv_documents_facts_status"), "cv_documents", type_="check")
    op.drop_constraint(op.f("ck_cv_documents_extraction_method"), "cv_documents", type_="check")
    op.drop_constraint(op.f("ck_cv_documents_extraction_status"), "cv_documents", type_="check")
    op.drop_column("cv_documents", "facts_status")
    op.drop_column("cv_documents", "extraction_method")
    op.execute(
        "UPDATE cv_documents SET extraction_status = 'extracting' "
        "WHERE extraction_status = 'processing'"
    )
    op.alter_column(
        "cv_documents", "extraction_error_code", new_column_name="error_code"
    )
    op.alter_column("cv_documents", "extraction_status", new_column_name="status")
    op.create_check_constraint(
        op.f("ck_cv_documents_status"),
        "cv_documents",
        "status IN ('pending', 'extracting', 'ready', 'error')",
    )
