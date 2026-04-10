import threading

from memory import extract_and_persist_memories


def schedule_memory_persistence(messages: list[dict], user_id: str) -> None:
    def _worker() -> None:
        extract_and_persist_memories(messages, user_id)

    threading.Thread(target=_worker, daemon=True).start()
