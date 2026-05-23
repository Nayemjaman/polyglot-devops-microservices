import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IdempotencyRecord


def request_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


async def get_record(
    session: AsyncSession,
    user_id: uuid.UUID,
    endpoint: str,
    key: str | None,
    payload: Any,
) -> IdempotencyRecord | None:
    if not key:
        return None
    record = await session.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.user_id == user_id,
            IdempotencyRecord.endpoint == endpoint,
            IdempotencyRecord.key == key,
            IdempotencyRecord.expires_at > datetime.now(timezone.utc),
        )
    )
    if record and record.request_hash != request_hash(payload):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Idempotency-Key was already used with a different request body"},
        )
    return record


async def save_record(
    session: AsyncSession,
    user_id: uuid.UUID,
    endpoint: str,
    key: str | None,
    payload: Any,
    resource_type: str,
    resource_id: uuid.UUID,
) -> None:
    if not key:
        return
    session.add(
        IdempotencyRecord(
            user_id=user_id,
            endpoint=endpoint,
            key=key,
            request_hash=request_hash(payload),
            resource_type=resource_type,
            resource_id=resource_id,
        )
    )
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Idempotency-Key is already being processed"},
        ) from None
