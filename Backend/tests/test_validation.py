import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_generation_request_validation(async_client: AsyncClient):
    """Test validation errors for invalid generation requests."""
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
