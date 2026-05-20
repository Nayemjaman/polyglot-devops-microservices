import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_http_client, get_settings_from_app
from app.core.config import get_settings
from app.main import create_app


def make_test_app(auth_response: httpx.Response):
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/auth/me"
        return auth_response

    app = create_app()
    settings = get_settings()
    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    async def settings_override():
        return settings

    async def http_client_override():
        return http_client

    app.dependency_overrides[get_settings_from_app] = settings_override
    app.dependency_overrides[get_http_client] = http_client_override
    app.state.test_http_client = http_client
    return app


@pytest.mark.asyncio
async def test_hello_requires_authorization() -> None:
    app = make_test_app(httpx.Response(200))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/hello")

    assert response.status_code == 401
    assert response.json()["message"] == "fuck you you are not authentivated"
    await app.state.test_http_client.aclose()


@pytest.mark.asyncio
async def test_hello_returns_authenticated_user_name() -> None:
    app = make_test_app(
        httpx.Response(
            200,
            json={
                "user": {
                    "first_name": "Nayem",
                    "last_name": "Hasan",
                }
            },
        )
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/hello", headers={"Authorization": "Bearer token"})

    assert response.status_code == 200
    assert response.json() == {"message": "hello Nayem Hasan", "service": "transaction-service"}
    await app.state.test_http_client.aclose()


@pytest.mark.asyncio
async def test_hello_rejects_invalid_token() -> None:
    app = make_test_app(httpx.Response(401, json={"detail": "Invalid or expired access token."}))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/hello", headers={"Authorization": "Bearer expired"})

    assert response.status_code == 401
    assert response.json()["message"] == "fuck you you are not authentivated"
    await app.state.test_http_client.aclose()
