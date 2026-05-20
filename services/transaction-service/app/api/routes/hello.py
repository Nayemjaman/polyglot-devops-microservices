import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.api.dependencies import get_http_client, get_settings_from_app
from app.clients.auth import AuthClient, AuthServiceUnavailable
from app.core.config import Settings
from app.schemas.common import MessageResponse

router = APIRouter(tags=["hello"])


@router.get("/hello", response_model=MessageResponse)
async def hello(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings_from_app),
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> MessageResponse:
    if not authorization:
        raise_unauthenticated()

    auth_client = AuthClient(settings=settings, http_client=http_client)
    try:
        user = await auth_client.get_current_user(authorization)
    except AuthServiceUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="failed to verify authentication",
        ) from exc

    if user is None:
        raise_unauthenticated()

    full_name = f"{user.first_name} {user.last_name}".strip()
    return MessageResponse(message=f"hello {full_name}", service="transaction-service")


def raise_unauthenticated() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="fuck you you are not authentivated",
    )
