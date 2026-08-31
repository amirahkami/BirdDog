from __future__ import annotations

import uuid
from pathlib import Path

import pymupdf
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.cv.processor import _process_item
from app.db.models import CVDocument, User, WorkItem
from app.db.session import engine
from app.main import app
from app.repositories import WorkItemRepository


client = TestClient(app)


@pytest.mark.integration
def test_complete_onboarding_and_cv_extraction(monkeypatch, tmp_path: Path) -> None:
    document_id = None
    user = User(
        keycloak_subject=f"onboarding-{uuid.uuid4()}",
        email=f"onboarding-{uuid.uuid4()}@example.invalid",
    )
    with Session(engine) as session, session.begin():
        session.add(user)
        session.flush()
        user_id = user.id
        subject = user.keycloak_subject
        email = user.email

    current_user = CurrentUser(
        id=user_id,
        subject=subject,
        username="test-jobseeker",
        email=email,
        display_name="Test Jobseeker",
        roles=frozenset({"jobseeker"}),
    )
    app.dependency_overrides[get_current_user] = lambda: current_user
    monkeypatch.setattr("app.routers.onboarding.settings.cv_storage_path", str(tmp_path))
    monkeypatch.setattr("app.cv.processor.settings.cv_storage_path", str(tmp_path))

    try:
        assert client.get("/onboarding").json()["steps"] == {
            "role": False,
            "preferences": False,
            "cv": False,
        }
        assert client.put("/onboarding/preferences", json=_preferences()).status_code == 409

        role = client.put("/onboarding/role", json={"desired_role": "  UI/UX Designer  "})
        assert role.status_code == 200
        assert role.json()["desired_role"] == "UI/UX Designer"

        invalid_preferences = _preferences() | {
            "accepts_hybrid": False,
            "accepts_remote": False,
        }
        assert client.put("/onboarding/preferences", json=invalid_preferences).status_code == 422

        preferences = client.put("/onboarding/preferences", json=_preferences())
        assert preferences.status_code == 200
        assert preferences.json()["steps"]["preferences"] is True
        assert preferences.json()["onsite_countries"] == ["DE"]
        assert preferences.json()["remote_countries"] == ["DE", "AT"]

        invalid_upload = client.post(
            "/onboarding/cv",
            files={"file": ("cv.pdf", b"not-a-pdf", "application/pdf")},
        )
        assert invalid_upload.status_code == 422
        assert invalid_upload.json()["detail"]["code"] == "invalid_signature"

        upload = client.post(
            "/onboarding/cv",
            files={"file": ("lebenslauf.pdf", _pdf_bytes(), "application/pdf")},
        )
        assert upload.status_code == 202
        assert upload.json()["status"] == "processing"
        assert upload.json()["cv"]["extraction_status"] == "pending"

        with Session(engine) as session, session.begin():
            document = session.scalar(
                select(CVDocument).where(
                    CVDocument.user_id == user_id,
                    CVDocument.is_current.is_(True),
                )
            )
            assert document is not None
            item = WorkItemRepository.claim(
                session,
                worker_id="test-worker",
                kind="cv.extract",
                limit=1,
            )[0]
            document_id = document.id
            extraction_item_id = item.id

        _process_item(extraction_item_id)

        status_response = client.get("/onboarding")
        assert status_response.status_code == 200
        body = status_response.json()
        assert body["cv"]["extraction_status"] == "ready"
        assert body["cv"]["extraction_method"] == "native"
        assert body["cv"]["detected_language"] == "en"
        assert body["cv"]["facts_status"] == "queued"
        assert body["status"] == "processing"

        with Session(engine) as session:
            document = session.get_one(CVDocument, document_id)
            assert "product design" in document.extracted_text.lower()
            assert session.scalar(
                select(WorkItem).where(
                    WorkItem.kind == "cv.facts",
                    WorkItem.subject_id == document_id,
                )
            ) is not None

        # Replacing the CV auto-cleans the previous one (row, facts, work items).
        replacement = client.post(
            "/onboarding/cv",
            files={"file": ("neu.pdf", _pdf_bytes(), "application/pdf")},
        )
        assert replacement.status_code == 202
        with Session(engine) as session:
            remaining = session.scalars(
                select(CVDocument.id).where(CVDocument.user_id == user_id)
            ).all()
            assert len(remaining) == 1
            assert document_id not in remaining
            assert (
                session.scalar(
                    select(WorkItem).where(WorkItem.subject_id == document_id)
                )
                is None
            )
    finally:
        app.dependency_overrides.clear()
        with Session(engine) as session, session.begin():
            cv_ids = session.scalars(
                select(CVDocument.id).where(CVDocument.user_id == user_id)
            ).all()
            if cv_ids:
                session.execute(delete(WorkItem).where(WorkItem.subject_id.in_(cv_ids)))
            session.execute(delete(User).where(User.id == user_id))


def _preferences() -> dict:
    return {
        "home_label": "München, Germany",
        "home_city": "München",
        "home_country_code": "de",
        "home_latitude": 48.137154,
        "home_longitude": 11.576124,
        "travel_radius_km": 50,
        "accepts_onsite": False,
        "accepts_hybrid": True,
        "accepts_remote": True,
        "accepts_full_time": True,
        "accepts_part_time": False,
        "onsite_countries": ["de"],
        "remote_countries": ["de", "at"],
    }


def _pdf_bytes() -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_textbox(
        page.rect + (50, 50, -50, -50),
        "Curriculum Vitae. Work experience and education. Responsible for product design and user research. Skills include Figma and prototyping. English and German knowledge.",
        fontsize=12,
    )
    data = document.tobytes()
    document.close()
    return data
