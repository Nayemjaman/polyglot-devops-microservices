import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_attachment_storage, get_db_session
from app.main import app
from app.main import create_app


@pytest.mark.asyncio
async def test_health_check() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "transaction-service"}


@pytest.mark.asyncio
async def test_storage_health_check() -> None:
    class Storage:
        async def check_bucket(self):
            return None

    async def storage_override():
        return Storage()

    test_app = create_app()
    test_app.dependency_overrides[get_attachment_storage] = storage_override

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.get("/health/storage")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "transaction-service"}


@pytest.mark.asyncio
async def test_database_health_check() -> None:
    class Session:
        async def execute(self, statement):
            return None

    async def db_session_override():
        yield Session()

    test_app = create_app()
    test_app.dependency_overrides[get_db_session] = db_session_override

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "transaction-service"}
