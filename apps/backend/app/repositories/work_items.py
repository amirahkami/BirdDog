import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import WorkItem


class WorkItemRepository:
    """PostgreSQL-backed durable work queue used by the Python workers."""

    @staticmethod
    def enqueue(
        session: Session,
        *,
        kind: str,
        idempotency_key: str,
        subject_type: str | None = None,
        subject_id: uuid.UUID | None = None,
        payload: dict[str, Any] | None = None,
        priority: int = 0,
        max_attempts: int = 3,
        available_at: datetime | None = None,
    ) -> tuple[WorkItem, bool]:
        item_id = uuid.uuid4()
        values: dict[str, Any] = {
            "id": item_id,
            "kind": kind,
            "idempotency_key": idempotency_key,
            "subject_type": subject_type,
            "subject_id": subject_id,
            "payload": payload or {},
            "priority": priority,
            "max_attempts": max_attempts,
        }
        if available_at is not None:
            values["available_at"] = available_at

        statement = (
            insert(WorkItem)
            .values(**values)
            .on_conflict_do_nothing(index_elements=["idempotency_key"])
            .returning(WorkItem.id)
        )
        inserted_id = session.scalar(statement)
        if inserted_id is not None:
            return session.get_one(WorkItem, inserted_id), True

        existing = session.scalar(
            select(WorkItem).where(WorkItem.idempotency_key == idempotency_key)
        )
        if existing is None:
            raise RuntimeError("work item conflict did not return an existing row")
        return existing, False

    @staticmethod
    def claim(
        session: Session,
        *,
        worker_id: str,
        kind: str | None = None,
        limit: int = 1,
        now: datetime | None = None,
    ) -> list[WorkItem]:
        if limit < 1:
            raise ValueError("limit must be at least 1")

        claimed_at = now or datetime.now(timezone.utc)
        conditions = [
            WorkItem.status == "queued",
            WorkItem.available_at <= claimed_at,
        ]
        if kind is not None:
            conditions.append(WorkItem.kind == kind)
        statement: Select[tuple[WorkItem]] = (
            select(WorkItem)
            .where(*conditions)
            .order_by(
                WorkItem.priority.desc(),
                WorkItem.available_at,
                WorkItem.created_at,
                WorkItem.id,
            )
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        items = list(session.scalars(statement))
        for item in items:
            item.status = "running"
            item.locked_at = claimed_at
            item.locked_by = worker_id
            item.attempts += 1
        session.flush()
        return items

    @staticmethod
    def release_stale(
        session: Session,
        *,
        stale_before: datetime,
        kind: str | None = None,
    ) -> int:
        conditions = [
            WorkItem.status == "running",
            WorkItem.locked_at < stale_before,
        ]
        if kind is not None:
            conditions.append(WorkItem.kind == kind)
        items = list(
            session.scalars(select(WorkItem).where(*conditions).with_for_update(skip_locked=True))
        )
        for item in items:
            item.status = "dead" if item.attempts >= item.max_attempts else "queued"
            item.locked_at = None
            item.locked_by = None
            item.last_error = "Worker lease expired"
        session.flush()
        return len(items)

    @staticmethod
    def complete(item: WorkItem, *, now: datetime | None = None) -> None:
        if item.status != "running":
            raise ValueError("only running work can be completed")
        item.status = "completed"
        item.completed_at = now or datetime.now(timezone.utc)
        item.locked_at = None
        item.locked_by = None
        item.last_error = None

    @staticmethod
    def fail(
        item: WorkItem,
        *,
        error: str,
        retry_at: datetime | None = None,
    ) -> None:
        if item.status != "running":
            raise ValueError("only running work can fail")
        item.last_error = error[:4000]
        item.locked_at = None
        item.locked_by = None
        if retry_at is not None and item.attempts < item.max_attempts:
            item.status = "queued"
            item.available_at = retry_at
        elif item.attempts >= item.max_attempts:
            item.status = "dead"
        else:
            item.status = "failed"
