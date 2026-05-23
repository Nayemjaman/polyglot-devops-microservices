import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OutboxEvent

PENDING = "PENDING"
PUBLISHED = "PUBLISHED"
FAILED = "FAILED"


async def enqueue_event(
    session: AsyncSession,
    *,
    aggregate_type: str,
    aggregate_id: uuid.UUID,
    routing_key: str,
    payload: dict[str, Any],
) -> OutboxEvent:
    event = OutboxEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        routing_key=routing_key,
        payload=payload,
    )
    session.add(event)
    await session.flush()
    return event


async def get_publishable_events(session: AsyncSession, batch_size: int) -> list[OutboxEvent]:
    now = datetime.now(timezone.utc)
    result = await session.scalars(
        select(OutboxEvent)
        .where(
            OutboxEvent.status.in_([PENDING, FAILED]),
            OutboxEvent.next_attempt_at <= now,
        )
        .order_by(OutboxEvent.created_at.asc())
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    return list(result)


def mark_published(event: OutboxEvent) -> None:
    now = datetime.now(timezone.utc)
    event.status = PUBLISHED
    event.published_at = now
    event.updated_at = now
    event.last_error = None


def mark_failed(event: OutboxEvent, error: Exception, max_attempts: int) -> None:
    attempts = event.attempts + 1
    delay_seconds = min(300, 2 ** min(attempts, 8))
    now = datetime.now(timezone.utc)
    event.attempts = attempts
    event.status = FAILED
    event.last_error = str(error)[:2000]
    event.updated_at = now
    event.next_attempt_at = now + timedelta(seconds=delay_seconds)
    if attempts >= max_attempts:
        event.next_attempt_at = now + timedelta(minutes=15)
