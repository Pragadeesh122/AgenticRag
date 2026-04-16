import pytest

import api.server as server_module
from database.models import UserMemoryFact


@pytest.mark.asyncio
async def test_get_chat_memory_returns_atomic_facts(async_client):
    response = await async_client.get("/chat/memory")

    assert response.status_code == 200
    assert response.json() == {"facts": []}


@pytest.mark.asyncio
async def test_create_and_delete_chat_memory_fact(async_client, session_factory, test_user, monkeypatch):
    monkeypatch.setattr(server_module, "_embed", lambda text: [0.0] * 1536)

    create_response = await async_client.post(
        "/chat/memory",
        json={"text": "Prefers concise explanations"},
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["text"] == "Prefers concise explanations"
    assert created["source_session_id"] == "manual-memory"

    list_response = await async_client.get("/chat/memory")
    assert list_response.status_code == 200
    assert [fact["text"] for fact in list_response.json()["facts"]] == [
        "Prefers concise explanations"
    ]

    async with session_factory() as session:
        stored = await session.get(UserMemoryFact, created["id"])
        assert stored is not None
        assert stored.user_id == test_user.id
        assert stored.superseded_at is None

    delete_response = await async_client.delete(f"/chat/memory/{created['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": "ok"}

    after_delete = await async_client.get("/chat/memory")
    assert after_delete.status_code == 200
    assert after_delete.json() == {"facts": []}

    async with session_factory() as session:
        stored = await session.get(UserMemoryFact, created["id"])
        assert stored is not None
        assert stored.superseded_at is not None


@pytest.mark.asyncio
async def test_create_chat_memory_fact_reuses_exact_active_duplicate(async_client, monkeypatch):
    monkeypatch.setattr(server_module, "_embed", lambda text: [0.0] * 1536)

    first = await async_client.post(
        "/chat/memory",
        json={"text": "Builds AgenticRag with FastAPI"},
    )
    second = await async_client.post(
        "/chat/memory",
        json={"text": "Builds AgenticRag with FastAPI"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
