import pytest
from sqlalchemy import inspect, text

from app.db.session import engine

EXPECTED_TABLES = {
    "alembic_version",
    "companies",
    "cover_letters",
    "cvs",
    "jobs",
    "matches",
    "niches",
    "users",
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
