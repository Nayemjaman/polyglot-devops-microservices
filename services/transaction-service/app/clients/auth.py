from typing import Any

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
        try:
            response = await self._http_client.get(url, headers={"Authorization": authorization})
        except httpx.HTTPError as exc:
            raise AuthServiceUnavailable from exc

        if response.status_code != 200:
            return None

        try:
            payload: dict[str, Any] = response.json()
            return AuthMeResponse.model_validate(payload).user
        except (ValueError, ValidationError) as exc:
            raise AuthServiceUnavailable from exc
