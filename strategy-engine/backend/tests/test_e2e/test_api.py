"""
Tests for the FastAPI endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_health_check(client: AsyncClient):
    """Health endpoint should return service info."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Strategy Engine" in data["service"]


@pytest.mark.anyio
async def test_start_pipeline(client: AsyncClient):
    """Starting a pipeline should return a run_id."""
    response = await client.post(
        "/api/pipeline/start",
        json={
            "raw_text": "ซื้อเก้าอี้ 5000 บาท แต่สูง 150 ซม เท้าลอย ปวดหลังมาก",
            "model": "gpt-4o",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["status"] == "pending"


@pytest.mark.anyio
async def test_start_pipeline_short_text_rejected(client: AsyncClient):
    """Pipeline should reject input shorter than 10 chars."""
    response = await client.post(
        "/api/pipeline/start",
        json={"raw_text": "short"},
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.anyio
async def test_get_status_not_found(client: AsyncClient):
    """Getting status of nonexistent run should 404."""
    response = await client.get("/api/pipeline/nonexistent-id/status")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_list_pipelines_empty(client: AsyncClient):
    """Listing pipelines when empty should return empty list."""
    response = await client.get("/api/pipeline/")
    assert response.status_code == 200
    # May contain runs from other tests; just check it's a list
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_blueprint_not_found(client: AsyncClient):
    """Getting nonexistent blueprint should 404."""
    response = await client.get("/api/blueprints/nonexistent-id")
    assert response.status_code == 404
