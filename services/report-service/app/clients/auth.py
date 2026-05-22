import uuid
import asyncio
from dataclasses import dataclass

import httpx


class AuthError(Exception):
    pass


@dataclass(frozen=True)
class AuthUser:
    id: uuid.UUID
    first_name: str
    last_name: str


async def get_authenticated_user(
    client: httpx.AsyncClient,
    auth_service_url: str,
    authorization: str,
) -> AuthUser:
    response = await _get_with_retry(client, f"{auth_service_url}/auth/me", authorization)
    if response.status_code != 200:
        raise AuthError("Invalid authentication token")

    payload = response.json()
    user = payload.get("user") or {}
    return AuthUser(
        id=uuid.UUID(str(user["id"])),
        first_name=user.get("first_name") or "",
        last_name=user.get("last_name") or "",
    )


async def _get_with_retry(client: httpx.AsyncClient, url: str, authorization: str) -> httpx.Response:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = await client.get(url, headers={"Authorization": authorization})
            if response.status_code < 500:
                return response
            last_error = AuthError(f"auth service returned {response.status_code}")
        except httpx.HTTPError as exc:
            last_error = exc
        if attempt < 2:
            await asyncio.sleep(0.1 * (2**attempt))
    raise AuthError("Auth service unavailable") from last_error
