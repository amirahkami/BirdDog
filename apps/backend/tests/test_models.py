from app.db import models  # noqa: F401
from app.db.base import Base


EXPECTED_TABLES = {
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


def test_expected_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_expected_relationship_constraints_exist() -> None:
    assert Base.metadata.tables["user_profiles"].c.user_id.unique is True
    assert Base.metadata.tables["role_pools"].c.primary_role_id.unique is True
    assert Base.metadata.tables["source_job_observations"].c.canonical_job_id.unique is None

    current_cv_index = next(
        index
        for index in Base.metadata.tables["cv_documents"].indexes
        if index.name == "uq_cv_documents_current_user"
    )
    assert current_cv_index.unique is True
    assert current_cv_index.dialect_options["postgresql"]["where"] is not None


def test_source_observations_and_canonical_jobs_are_separate() -> None:
    observation = Base.metadata.tables["source_job_observations"]
    assert "raw_payload" in observation.c
    assert "canonical_job_id" in observation.c
    assert "raw_payload" not in Base.metadata.tables["canonical_jobs"].c


def test_jobs_support_multiple_locations_and_pools() -> None:
    assert Base.metadata.tables["job_locations"].c.job_id.unique is None
    assert Base.metadata.tables["pool_jobs"].c.job_id.unique is None
