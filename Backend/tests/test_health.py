import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check_endpoint(async_client: AsyncClient):
    """Test health check returns 200 with service information."""
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "services" in data
    assert data["database"]["status"] == "connected"

@pytest.mark.asyncio
async def test_settings_endpoint(async_client: AsyncClient):
    """Test settings endpoint returns non-sensitive metadata."""
    response = await async_client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert "providers" in data
    assert "models" in data
    # Ensure no secret keys are exposed
    assert "api_key" not in str(data).lower()
