from __future__ import annotations

import asyncio
import io
import os
import time
import uuid

import pymupdf
import pytest
from fastapi import UploadFile
from sqlalchemy import delete
from sqlalchemy.orm import Session
from starlette.datastructures import Headers

from app.core.config import get_settings
from app.cv import CVStorage
from app.db.models import CVDocument, User, WorkItem
from app.db.session import engine
from app.repositories import WorkItemRepository


@pytest.mark.integration
@pytest.mark.external_worker
@pytest.mark.skipif(
    os.environ.get("RUN_EXTERNAL_WORKER_TEST") != "1",
    reason="requires the running Docker Compose worker",
)
def test_running_worker_extracts_queued_cv() -> None:
    settings = get_settings()
    storage = CVStorage(
        settings.cv_storage_path,
        maximum_bytes=settings.cv_max_bytes,
        maximum_pages=settings.cv_max_pages,
    )
    user = User(
        keycloak_subject=f"worker-smoke-{uuid.uuid4()}",
        email=f"worker-smoke-{uuid.uuid4()}@example.invalid",
    )
    with Session(engine) as session, session.begin():
        session.add(user)
        session.flush()
        user_id = user.id

    stored = asyncio.run(
        storage.store(
            UploadFile(
                file=io.BytesIO(_pdf_bytes()),
                filename="worker-smoke.pdf",
                headers=Headers({"content-type": "application/pdf"}),
            ),
            user_id=user_id,
        )
    )
    document_id = None
    try:
        with Session(engine) as session, session.begin():
            document = CVDocument(
                user_id=user_id,
                original_filename=stored.original_filename,
                content_type="application/pdf",
                byte_size=stored.byte_size,
                page_count=stored.page_count,
                sha256=stored.sha256,
                storage_key=stored.storage_key,
            )
            session.add(document)
            session.flush()
            document_id = document.id
            WorkItemRepository.enqueue(
                session,
                kind="cv.extract",
                idempotency_key=f"cv.extract:{document.id}:{document.sha256}",
                subject_type="cv_document",
                subject_id=document.id,
                payload={"cv_document_id": str(document.id)},
                max_attempts=2,
            )

        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            with Session(engine) as session:
                document = session.get_one(CVDocument, document_id)
                if document.extraction_status in {"ready", "error"}:
                    break
            time.sleep(0.25)

        with Session(engine) as session:
            document = session.get_one(CVDocument, document_id)
            assert document.extraction_status == "ready"
            assert document.extraction_method == "native"
            assert document.facts_status == "queued"
            normalized_text = " ".join(document.extracted_text.lower().split())
            assert "user research" in normalized_text
    finally:
        with Session(engine) as session, session.begin():
            if document_id is not None:
                session.execute(delete(WorkItem).where(WorkItem.subject_id == document_id))
            session.execute(delete(User).where(User.id == user_id))
        storage.delete(stored.storage_key)


def _pdf_bytes() -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_textbox(
        page.rect + (50, 50, -50, -50),
        "Curriculum Vitae. Work experience and education. Responsible for product design and user research. Skills and knowledge include Figma, prototyping and English.",
        fontsize=12,
    )
    data = document.tobytes()
    document.close()
    return data
