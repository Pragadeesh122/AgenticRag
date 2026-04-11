import pytest

from tasks import memory_tasks


class _FakeRedis:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value, ex=None, nx=False):
        if nx and key in self.data:
            return False
        self.data[key] = value
        return True

    def delete(self, key):
        self.data.pop(key, None)


@pytest.mark.asyncio
async def test_memory_task_is_idempotent(monkeypatch):
    calls = []
    fake_redis = _FakeRedis()

    monkeypatch.setattr(memory_tasks, "redis_client", fake_redis)
    monkeypatch.setattr(
        memory_tasks,
        "extract_and_persist_memories",
        lambda messages, user_id: calls.append((user_id, messages)),
    )

    messages = [{"role": "user", "content": "Remember I like dashboards."}]

    first = await memory_tasks.persist_memories_task({}, "user-1", messages)
    second = await memory_tasks.persist_memories_task({}, "user-1", messages)

    assert first["status"] == "ok"
    assert second["status"] == "skipped"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_memory_task_can_retry_after_transient_failure(monkeypatch):
    attempts = {"count": 0}
    fake_redis = _FakeRedis()

    def flaky_extract(messages, user_id):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary failure")

    monkeypatch.setattr(memory_tasks, "redis_client", fake_redis)
    monkeypatch.setattr(memory_tasks, "extract_and_persist_memories", flaky_extract)

    messages = [{"role": "assistant", "content": "You prefer markdown exports."}]

    with pytest.raises(RuntimeError):
        await memory_tasks.persist_memories_task({}, "user-2", messages)

    result = await memory_tasks.persist_memories_task({}, "user-2", messages)

    assert result["status"] == "ok"
    assert attempts["count"] == 2
