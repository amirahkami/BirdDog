from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import (
    AIModel,
    AIProvider,
    AIRoute,
    CVDocument,
    CanonicalJob,
    JobLocation,
    PoolJob,
    RoleConcept,
    RolePool,
    SourceAdapter,
    SourceBoard,
    SourceJobObservation,
    User,
    UserJobAction,
    UserMatch,
    UserPoolMembership,
    UserProfile,
    WorkItem,
)
from app.db.session import engine
from app.repositories import WorkItemRepository


@pytest.mark.integration
def test_one_job_can_keep_multiple_source_observations_locations_and_pools() -> None:
    with Session(engine) as session, session.begin():
        role_a = RoleConcept(
            preferred_label="UI/UX Designer",
            normalized_label=f"ui ux designer {uuid.uuid4()}",
            status="approved",
        )
        role_b = RoleConcept(
            preferred_label="Product Designer",
            normalized_label=f"product designer {uuid.uuid4()}",
            status="approved",
        )
        session.add_all([role_a, role_b])
        session.flush()
        pool_a = RolePool(primary_role_id=role_a.id, slug=f"uiux-{uuid.uuid4()}", status="active")
        pool_b = RolePool(primary_role_id=role_b.id, slug=f"product-{uuid.uuid4()}", status="active")
        session.add_all([pool_a, pool_b])

        job = CanonicalJob(
            company_name="Example GmbH",
            normalized_company="example gmbh",
            title="Product Designer",
            normalized_title="product designer",
            application_url="https://example.invalid/jobs/1",
        )
        session.add(job)
        session.flush()
        session.add_all(
            [
                JobLocation(
                    job_id=job.id,
                    label="München, Germany",
                    city="München",
                    country_code="DE",
                    workplace_type="hybrid",
                ),
                JobLocation(
                    job_id=job.id,
                    label="European remote",
                    workplace_type="remote",
                    remote_scope="eu_eea_ch",
                ),
                PoolJob(pool_id=pool_a.id, job_id=job.id, status="active", linked_by="rules"),
                PoolJob(pool_id=pool_b.id, job_id=job.id, status="active", linked_by="admin"),
            ]
        )

        adapter = SourceAdapter(
            code=f"test-{uuid.uuid4()}",
            name="Test ATS",
            layer="primary",
            terms_status="approved",
            enabled=True,
        )
        session.add(adapter)
        session.flush()
        board_a = SourceBoard(adapter_id=adapter.id, external_key=f"a-{uuid.uuid4()}", name="A")
        board_b = SourceBoard(adapter_id=adapter.id, external_key=f"b-{uuid.uuid4()}", name="B")
        session.add_all([board_a, board_b])
        session.flush()
        session.add_all(
            [
                SourceJobObservation(
                    board_id=board_a.id,
                    canonical_job_id=job.id,
                    external_id="job-1",
                    title=job.title,
                    company_name=job.company_name,
                    source_url="https://example.invalid/source/a",
                    application_url=job.application_url,
                    content_hash="a" * 64,
                ),
                SourceJobObservation(
                    board_id=board_b.id,
                    canonical_job_id=job.id,
                    external_id="job-2",
                    title=job.title,
                    company_name=job.company_name,
                    source_url="https://example.invalid/source/b",
                    application_url=job.application_url,
                    content_hash="b" * 64,
                ),
            ]
        )
        session.flush()

        assert session.scalar(
            select(func.count()).select_from(JobLocation).where(JobLocation.job_id == job.id)
        ) == 2
        assert session.scalar(
            select(func.count()).select_from(PoolJob).where(PoolJob.job_id == job.id)
        ) == 2
        assert session.scalar(
            select(func.count())
            .select_from(SourceJobObservation)
            .where(SourceJobObservation.canonical_job_id == job.id)
        ) == 2

        session.rollback()


@pytest.mark.integration
def test_ready_profile_requires_work_mode() -> None:
    with Session(engine) as session:
        user = User(
            keycloak_subject=f"test-{uuid.uuid4()}",
            email=f"test-{uuid.uuid4()}@example.invalid",
        )
        session.add(user)
        session.flush()
        session.add(
            UserProfile(
                user_id=user.id,
                desired_role_text="UI/UX Designer",
                onboarding_status="ready",
                accepts_onsite=False,
                accepts_hybrid=False,
                accepts_remote=False,
                accepts_full_time=True,
            )
        )
        with pytest.raises(IntegrityError):
            session.flush()
        session.rollback()


@pytest.mark.integration
def test_profile_cv_ai_pool_match_and_action_chain() -> None:
    with Session(engine) as session, session.begin():
        user = User(
            keycloak_subject=f"test-{uuid.uuid4()}",
            email=f"test-{uuid.uuid4()}@example.invalid",
            preferred_language="de",
        )
        provider = AIProvider(
            code=f"test-{uuid.uuid4()}",
            name="Test provider",
            adapter_type="openai_compatible",
            base_url="https://example.invalid/api/v1",
            enabled=True,
        )
        session.add_all([user, provider])
        session.flush()
        model = AIModel(
            provider_id=provider.id,
            external_model_id="test-model",
            display_name="Test model",
            enabled=True,
            supported_tasks=["candidate_facts", "job_facts"],
            benchmark_status="approved",
        )
        session.add(model)
        session.flush()
        session.add(AIRoute(task="candidate_facts", primary_model_id=model.id))
        session.add(
            UserProfile(
                user_id=user.id,
                desired_role_text="UI/UX Designer",
                home_label="München, Germany",
                home_city="München",
                home_country_code="DE",
                home_latitude=48.137154,
                home_longitude=11.576124,
                accepts_remote=True,
                onboarding_status="ready",
            )
        )
        session.add(
            CVDocument(
                user_id=user.id,
                facts_model_id=model.id,
                original_filename="lebenslauf.pdf",
                content_type="application/pdf",
                byte_size=1024,
                page_count=2,
                sha256="a" * 64,
                storage_key=f"private/{uuid.uuid4()}.pdf",
                extraction_status="ready",
                extraction_method="native",
                detected_language="de",
                facts={"skills": ["Figma"]},
                evidence={"skills": ["Figma"]},
            )
        )
        role = RoleConcept(
            preferred_label="User interface designer",
            normalized_label=f"user interface designer {uuid.uuid4()}",
            taxonomy="esco",
            taxonomy_version="1.2.1",
            esco_uri=f"https://data.europa.eu/esco/occupation/{uuid.uuid4()}",
            status="approved",
        )
        session.add(role)
        session.flush()
        pool = RolePool(primary_role_id=role.id, slug=f"uiux-{uuid.uuid4()}", status="active")
        session.add(pool)
        session.flush()
        session.add(
            UserPoolMembership(
                user_id=user.id,
                pool_id=pool.id,
                desired_role_text="UI/UX Designer",
                status="active",
            )
        )
        job = CanonicalJob(
            facts_model_id=model.id,
            company_name="Design GmbH",
            normalized_company="design gmbh",
            title="UI/UX Designer",
            normalized_title="ui ux designer",
            application_url="https://example.invalid/jobs/uiux",
            facts_status="ready",
        )
        session.add(job)
        session.flush()
        session.add(PoolJob(pool_id=pool.id, job_id=job.id, status="active", linked_by="rules"))
        session.add(
            UserMatch(
                user_id=user.id,
                job_id=job.id,
                pool_id=pool.id,
                score=88.5,
                tier="strong",
                eligibility="eligible",
                reasons=[{"code": "desired_role", "weight": 40}],
                algorithm_version="v1-test",
            )
        )
        session.add(
            UserJobAction(
                user_id=user.id,
                job_id=job.id,
                preference=None,
                last_application_opened_at=datetime.now(timezone.utc),
            )
        )
        session.flush()
        assert session.scalar(
            select(func.count()).select_from(UserMatch).where(UserMatch.user_id == user.id)
        ) == 1
        session.rollback()


@pytest.mark.integration
@pytest.mark.parametrize(
    ("byte_size", "page_count"),
    [(26214401, 1), (1024, 51)],
)
def test_cv_database_guardrails(byte_size: int, page_count: int) -> None:
    with Session(engine) as session:
        user = User(
            keycloak_subject=f"test-{uuid.uuid4()}",
            email=f"test-{uuid.uuid4()}@example.invalid",
        )
        session.add(user)
        session.flush()
        session.add(
            CVDocument(
                user_id=user.id,
                original_filename="cv.pdf",
                content_type="application/pdf",
                byte_size=byte_size,
                page_count=page_count,
                sha256="b" * 64,
                storage_key=f"private/{uuid.uuid4()}.pdf",
            )
        )
        with pytest.raises(IntegrityError):
            session.flush()
        session.rollback()


@pytest.mark.integration
def test_work_item_enqueue_is_idempotent() -> None:
    key = f"test-idempotency-{uuid.uuid4()}"
    with Session(engine) as session, session.begin():
        first, first_created = WorkItemRepository.enqueue(
            session,
            kind="test",
            idempotency_key=key,
            payload={"value": 1},
        )
        second, second_created = WorkItemRepository.enqueue(
            session,
            kind="test",
            idempotency_key=key,
            payload={"value": 2},
        )
        assert first.id == second.id
        assert first_created is True
        assert second_created is False
        session.rollback()


@pytest.mark.integration
def test_concurrent_workers_skip_locked_items() -> None:
    prefix = f"test-claim-{uuid.uuid4()}"
    item_ids: list[uuid.UUID] = []
    try:
        with Session(engine) as setup, setup.begin():
            for number in range(2):
                item, _ = WorkItemRepository.enqueue(
                    setup,
                    kind="test",
                    idempotency_key=f"{prefix}-{number}",
                    priority=number,
                )
                item_ids.append(item.id)

        first_session = Session(engine)
        second_session = Session(engine)
        try:
            first = WorkItemRepository.claim(first_session, worker_id="worker-a", limit=1)
            second = WorkItemRepository.claim(second_session, worker_id="worker-b", limit=2)
            assert len(first) == 1
            assert len(second) == 1
            assert first[0].id != second[0].id
            WorkItemRepository.complete(first[0])
            WorkItemRepository.fail(
                second[0],
                error="temporary failure",
                retry_at=datetime.now(timezone.utc) + timedelta(seconds=30),
            )
            first_session.commit()
            second_session.commit()

            with Session(engine) as verification:
                assert verification.get_one(WorkItem, first[0].id).status == "completed"
                assert verification.get_one(WorkItem, second[0].id).status == "queued"
        finally:
            first_session.close()
            second_session.close()
    finally:
        with Session(engine) as cleanup, cleanup.begin():
            for item_id in item_ids:
                item = cleanup.get(WorkItem, item_id)
                if item is not None:
                    cleanup.delete(item)
