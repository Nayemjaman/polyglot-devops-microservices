import uuid
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
    response = await client.get(
        f"{auth_service_url}/auth/me",
        headers={"Authorization": authorization},
    )
    if response.status_code != 200:
        raise AuthError("Invalid authentication token")

    payload = response.json()
    user = payload.get("user") or {}
    return AuthUser(
        id=uuid.UUID(str(user["id"])),
        first_name=user.get("first_name") or "",
        last_name=user.get("last_name") or "",
    )
