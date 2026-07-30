import pytest
from sqlalchemy import inspect, text

from app.db.session import engine

EXPECTED_TABLES = {
    "alembic_version",
    "ai_models",
    "ai_providers",
    "ai_routes",
    "canonical_jobs",
    "cv_documents",
    "job_locations",
    "pool_jobs",
    "role_aliases",
    "role_concepts",
    "role_pool_relations",
    "role_pools",
    "source_adapters",
    "source_boards",
    "source_job_observations",
    "source_runs",
    "user_job_actions",
    "user_matches",
    "user_pool_memberships",
    "user_profiles",
    "users",
    "work_items",
}


@pytest.mark.integration
def test_migrated_schema_and_vector_extension() -> None:
    inspector = inspect(engine)
    assert set(inspector.get_table_names()) == EXPECTED_TABLES

    with engine.connect() as connection:
        extension = connection.scalar(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        )

    assert extension == "vector"


@pytest.mark.integration
def test_schema_matches_sqlalchemy_metadata() -> None:
    from app.db import models  # noqa: F401
    from app.db.base import Base

    inspector = inspect(engine)
    for table_name, table in Base.metadata.tables.items():
        database_columns = {column["name"] for column in inspector.get_columns(table_name)}
        assert database_columns == set(table.c.keys())


@pytest.mark.integration
def test_users_remain_the_identity_root() -> None:
    inspector = inspect(engine)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    assert {"id", "keycloak_subject", "email", "preferred_language"} <= user_columns
