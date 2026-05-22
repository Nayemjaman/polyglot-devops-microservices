import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from redis.asyncio import Redis

from app.core.config import Settings


def _json_default(value: Any) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    return str(value)


class DashboardCache:
    def __init__(self, redis: Redis, settings: Settings) -> None:
        self.redis = redis
        self.ttl = settings.dashboard_cache_ttl_seconds

    def key(self, user_id: Any, year: int, month: int) -> str:
        return f"report:dashboard:{user_id}:{year}:{month}"

    async def get(self, user_id: Any, year: int, month: int) -> dict[str, Any] | None:
        raw = await self.redis.get(self.key(user_id, year, month))
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, user_id: Any, year: int, month: int, data: dict[str, Any]) -> None:
        await self.redis.setex(
            self.key(user_id, year, month),
            self.ttl,
            json.dumps(data, default=_json_default),
        )

    async def invalidate_user(self, user_id: Any) -> int:
        pattern = f"report:dashboard:{user_id}:*"
        deleted = 0
        async for key in self.redis.scan_iter(pattern):
            deleted += await self.redis.delete(key)
        return deleted


class NullDashboardCache:
    async def get(self, user_id: Any, year: int, month: int) -> dict[str, Any] | None:
        return None

    async def set(self, user_id: Any, year: int, month: int, data: dict[str, Any]) -> None:
        return None

    async def invalidate_user(self, user_id: Any) -> int:
        return 0
