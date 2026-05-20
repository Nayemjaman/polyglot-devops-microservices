import pytest
from fastapi.routing import APIRoute
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_user_id
from app.main import create_app


def test_all_api_routes_require_authenticated_user_dependency() -> None:
    app = create_app()
    unprotected_routes: list[str] = []

    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith("/api/"):
            continue

        has_auth_dependency = any(
            dependency.call is get_current_user_id
            for dependency in route.dependant.dependencies
        )
        if not has_auth_dependency:
            methods = ",".join(sorted(route.methods or []))
            unprotected_routes.append(f"{methods} {route.path}")

    assert unprotected_routes == []


@pytest.mark.asyncio
async def test_api_route_without_authorization_is_rejected() -> None:
    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/wallets")

    assert response.status_code == 401
    assert response.json() == {
        "success": False,
        "message": "authentication required",
        "errors": None,
    }
