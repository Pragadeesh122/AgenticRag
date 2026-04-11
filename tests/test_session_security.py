import re
import uuid

import pytest

from api import server as server_module
from database.models import ChatSession, User


@pytest.mark.asyncio
async def test_exists_endpoint_hides_non_owned_sessions(async_client, monkeypatch, test_user):
    monkeypatch.setattr(server_module, "session_owned_by_user", lambda *_: False)

    response = await async_client.get("/session/foreign-session/exists")

    assert response.status_code == 200
    assert response.json() == {"exists": False}


@pytest.mark.asyncio
async def test_chat_stream_returns_not_found_for_non_owned_session(async_client, monkeypatch):
    monkeypatch.setattr(server_module, "session_owned_by_user", lambda *_: False)

    response = await async_client.post(
        "/chat/stream",
        json={"sessionId": "foreign-session", "message": "hello"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


@pytest.mark.asyncio
async def test_delete_backend_session_returns_not_found_for_non_owned_session(
    async_client, monkeypatch
):
    monkeypatch.setattr(server_module, "session_owned_by_user", lambda *_: False)

    response = await async_client.delete("/chat/backend-session/foreign-session")

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


@pytest.mark.asyncio
async def test_restore_requires_owned_persisted_session(
    async_client,
    session_factory,
    monkeypatch,
):
    async with session_factory() as session:
        other_user = User(
            id=uuid.uuid4(),
            email="other@example.com",
            hashed_password="hashed",
            is_active=True,
            is_verified=True,
        )
        session.add(other_user)
        session.add(
            ChatSession(
                id=str(uuid.uuid4()),
                user_id=other_user.id,
                backend_session_id="foreign-session",
                title="Foreign chat",
            )
        )
        await session.commit()

    monkeypatch.setattr(server_module, "session_exists", lambda *_: False)

    response = await async_client.post(
        "/session/restore",
        json={
            "session_id": "foreign-session",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


@pytest.mark.asyncio
async def test_restore_succeeds_for_owned_persisted_session(
    async_client,
    session_factory,
    test_user,
    monkeypatch,
):
    async with session_factory() as session:
        session.add(
            ChatSession(
                id=str(uuid.uuid4()),
                user_id=test_user.id,
                backend_session_id="owned-session",
                title="Owned chat",
            )
        )
        await session.commit()

    restored = {}

    def fake_restore(session_id, messages, user_id="", project_name=""):
        restored["session_id"] = session_id
        restored["messages"] = messages
        restored["user_id"] = user_id
        restored["project_name"] = project_name

    monkeypatch.setattr(server_module, "session_exists", lambda *_: False)
    monkeypatch.setattr(server_module, "restore_session", fake_restore)

    response = await async_client.post(
        "/session/restore",
        json={
            "session_id": "owned-session",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )

    assert response.status_code == 200
    assert restored["session_id"] == "owned-session"
    assert restored["user_id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_rate_limit_triggers_on_chat_stream(async_client, monkeypatch):
    monkeypatch.setattr(server_module, "session_owned_by_user", lambda *_: True)
    monkeypatch.setattr(
        server_module,
        "chat_stream",
        lambda *_: iter(["event: done\ndata: {\"prompt_tokens\": 0}\n\n"]),
    )
    monkeypatch.setattr(
        server_module,
        "RATE_LIMIT_RULES",
        (
            {
                "name": "chat_stream_test",
                "method": "POST",
                "pattern": re.compile(r"^/chat/stream$"),
                "limit": 2,
                "window": 60,
            },
        ),
    )
    server_module._RATE_LIMIT_FALLBACK.clear()

    first = await async_client.post(
        "/chat/stream",
        json={"sessionId": "owned-session", "message": "one"},
    )
    second = await async_client.post(
        "/chat/stream",
        json={"sessionId": "owned-session", "message": "two"},
    )
    third = await async_client.post(
        "/chat/stream",
        json={"sessionId": "owned-session", "message": "three"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.json()["detail"] == "Rate limit exceeded"
