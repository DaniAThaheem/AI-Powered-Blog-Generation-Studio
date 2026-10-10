import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient
import app.api.routes.generations as gen_routes

@pytest.mark.asyncio
async def test_generation_request_validation(async_client: AsyncClient, monkeypatch):
    """Test validation errors for invalid generation requests."""
    # Stop valid POST from starting a real background generation
    mock_execute = AsyncMock()
    monkeypatch.setattr(gen_routes.generation_runner, "execute_generation", mock_execute)

    # Empty topic should fail validation
    res = await async_client.post("/api/generations", json={"topic": ""})
    assert res.status_code == 422

    # Topic too short (<3 chars)
    res = await async_client.post("/api/generations", json={"topic": "ab"})
    assert res.status_code == 422

    # Word count below minimum (<300)
    res = await async_client.post("/api/generations", json={
        "topic": "Advanced LangGraph Systems",
        "target_word_count": 50
    })
    assert res.status_code == 422

    # Valid payload should succeed and return 201
    res = await async_client.post("/api/generations", json={
        "topic": "Microservices Architecture in 2026",
        "audience": "Senior Architects",
        "tone": "Analytical",
        "blog_kind": "system_design",
        "target_word_count": 1500,
        "enable_research": False
    })
    assert res.status_code == 201
    data = res.json()
    assert data["topic"] == "Microservices Architecture in 2026"
    assert data["status"] in ("queued", "running")
    assert "id" in data
    assert "thread_id" in data
    mock_execute.assert_called_once()

@pytest.mark.asyncio
async def test_enable_hitl_creates_generation(async_client: AsyncClient, monkeypatch):
    """Verify that enable_hitl=True succeeds and enqueues generation in Phase 2."""
    mock_execute = AsyncMock()
    monkeypatch.setattr(gen_routes.generation_runner, "execute_generation", mock_execute)
    res = await async_client.post("/api/generations", json={
        "topic": "Event-Driven Microservices Architecture",
        "enable_hitl": True
    })
    assert res.status_code == 201
    assert res.json()["enable_hitl"] is True
