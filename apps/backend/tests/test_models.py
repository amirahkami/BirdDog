from app.db.base import Base
from app.db import models  # noqa: F401


def test_expected_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "companies",
        "cover_letters",
        "cvs",
        "jobs",
        "matches",
        "niches",
        "users",
    }


def test_expected_relationship_constraints_exist() -> None:
    assert Base.metadata.tables["cvs"].c.user_id.unique is True
    assert Base.metadata.tables["jobs"].c.dedup_key.unique is True
