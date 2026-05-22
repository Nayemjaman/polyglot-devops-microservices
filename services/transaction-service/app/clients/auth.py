from typing import Any
import asyncio

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.auth import AuthMeResponse, AuthUser


class AuthServiceUnavailable(Exception):
    pass


class AuthClient:
    def __init__(self, settings: Settings, http_client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._http_client = http_client

    async def get_current_user(self, authorization: str) -> AuthUser | None:
        url = f"{self._settings.auth_service_url}/auth/me"
        response = await self._get_with_retry(url, authorization)

        if response.status_code != 200:
            return None

        try:
            payload: dict[str, Any] = response.json()
            return AuthMeResponse.model_validate(payload).user
        except (ValueError, ValidationError) as exc:
            raise AuthServiceUnavailable from exc

    async def _get_with_retry(self, url: str, authorization: str) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = await self._http_client.get(
                    url,
                    headers={"Authorization": authorization},
                    timeout=self._settings.http_timeout_seconds,
                )
                if response.status_code < 500:
                    return response
                last_error = AuthServiceUnavailable(f"auth service returned {response.status_code}")
            except httpx.HTTPError as exc:
                last_error = exc
            if attempt < 2:
                await asyncio.sleep(0.1 * (2**attempt))
        raise AuthServiceUnavailable from last_error
