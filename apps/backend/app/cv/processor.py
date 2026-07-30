from __future__ import annotations

import logging
import os
import socket
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import get_settings
from app.cv.extraction import CVExtractionError, extract_pdf
from app.cv.storage import CVStorage, CVValidationError
from app.db.models import CVDocument, UserProfile, WorkItem
from app.db.session import SessionLocal
from app.repositories import WorkItemRepository


logger = logging.getLogger(__name__)
settings = get_settings()
worker_id = f"{socket.gethostname()}:{os.getpid()}:cv"


def process_cv_work_batch() -> None:
    now = datetime.now(timezone.utc)
    with SessionLocal() as session, session.begin():
        recovered = WorkItemRepository.release_stale(
            session,
            kind="cv.extract",
            stale_before=now - timedelta(minutes=10),
        )
        items = WorkItemRepository.claim(
            session,
            worker_id=worker_id,
            kind="cv.extract",
            limit=2,
            now=now,
        )
        item_ids = [item.id for item in items]
    if recovered:
        logger.warning("Recovered %s stale CV extraction work items", recovered)
    for item_id in item_ids:
        _process_item(item_id)


def _process_item(item_id) -> None:
    with SessionLocal() as session, session.begin():
        item = session.get(WorkItem, item_id)
        if item is None or item.status != "running" or item.subject_id is None:
            return
        document = session.get(CVDocument, item.subject_id)
        if document is None:
            WorkItemRepository.fail(item, error="CV document no longer exists")
            return
        document.extraction_status = "processing"
        document.extraction_error_code = None

    storage = CVStorage(
        settings.cv_storage_path,
        maximum_bytes=settings.cv_max_bytes,
        maximum_pages=settings.cv_max_pages,
    )
    try:
        path = storage.resolve(document.storage_key)
        result = extract_pdf(
            path,
            timeout_seconds=settings.cv_ocr_timeout_seconds,
            ocr_dpi=settings.cv_ocr_dpi,
        )
    except CVValidationError as error:
        _record_failure(item_id, error.code, str(error), retryable=False)
        return
    except CVExtractionError as error:
        _record_failure(item_id, error.code, str(error), retryable=error.retryable)
        return
    except Exception:
        logger.exception("Unexpected CV extraction failure for work item %s", item_id)
        _record_failure(
            item_id,
            "unexpected_extraction_error",
            "Unexpected CV extraction failure",
            retryable=True,
        )
        return

    with SessionLocal() as session, session.begin():
        item = session.get(WorkItem, item_id)
        document = session.get(CVDocument, item.subject_id) if item and item.subject_id else None
        if item is None or item.status != "running" or document is None:
            return
        document.extracted_text = result.text
        document.detected_language = result.language
        document.extraction_method = result.method
        document.extraction_status = "ready"
        document.extraction_error_code = None
        if document.is_current:
            document.facts_status = "queued"
            WorkItemRepository.enqueue(
                session,
                kind="cv.facts",
                idempotency_key=f"cv.facts:{document.id}:{document.sha256}",
                subject_type="cv_document",
                subject_id=document.id,
                payload={"cv_document_id": str(document.id)},
                max_attempts=3,
            )
            profile = session.scalar(
                select(UserProfile).where(UserProfile.user_id == document.user_id)
            )
            if profile is not None:
                profile.onboarding_status = "processing"
        WorkItemRepository.complete(item)


def _record_failure(item_id, code: str, message: str, *, retryable: bool) -> None:
    now = datetime.now(timezone.utc)
    with SessionLocal() as session, session.begin():
        item = session.get(WorkItem, item_id)
        document = session.get(CVDocument, item.subject_id) if item and item.subject_id else None
        if item is None or item.status != "running":
            return
        retry_at = None
        if retryable and item.attempts < item.max_attempts:
            retry_at = now + timedelta(seconds=min(60 * (2 ** (item.attempts - 1)), 600))
        WorkItemRepository.fail(item, error=message, retry_at=retry_at)
        if document is None:
            return
        document.extraction_status = "pending" if item.status == "queued" else "error"
        document.extraction_error_code = code
        if document.is_current and item.status != "queued":
            profile = session.scalar(
                select(UserProfile).where(UserProfile.user_id == document.user_id)
            )
            if profile is not None:
                profile.onboarding_status = "error"
