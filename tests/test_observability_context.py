import asyncio
import contextvars
import unittest

from observability.context import (
    clear_context,
    get_chat_type,
    get_project_hash,
    get_session_hash,
    get_user_hash,
    pop_context,
    push_context,
)
from observability.hash import stable_hash


class ObservabilityContextTests(unittest.TestCase):
    def setUp(self):
        clear_context()

    def tearDown(self):
        clear_context()

    def test_push_and_pop_context(self):
        tokens = push_context(
            chat_type="project",
            user_id="user-a",
            session_id="session-a",
            project_id="project-a",
        )
        self.assertEqual(get_chat_type(), "project")
        self.assertEqual(get_user_hash(), stable_hash("user-a"))
        self.assertEqual(get_session_hash(), stable_hash("session-a"))
        self.assertEqual(get_project_hash(), stable_hash("project-a"))

        pop_context(tokens)

        self.assertEqual(get_chat_type(), "unknown")
        self.assertEqual(get_user_hash(), "unknown")
        self.assertEqual(get_session_hash(), "unknown")
        self.assertEqual(get_project_hash(), "unknown")

    def test_async_context_isolation(self):
        async def worker(i: int):
            tokens = push_context(
                chat_type="general",
                user_id=f"user-{i}",
                session_id=f"session-{i}",
            )
            await asyncio.sleep(0)
            observed = (get_user_hash(), get_session_hash())
            pop_context(tokens)
            return observed

        async def run_workers():
            return await asyncio.gather(worker(1), worker(2))

        (u1, s1), (u2, s2) = asyncio.run(run_workers())
        self.assertNotEqual(u1, u2)
        self.assertNotEqual(s1, s2)
        self.assertEqual(get_chat_type(), "unknown")
        self.assertEqual(get_user_hash(), "unknown")
        self.assertEqual(get_session_hash(), "unknown")

    def test_pop_context_works_from_different_context_copy(self):
        previous = push_context(
            chat_type="general",
            user_id="user-x",
            session_id="session-x",
        )
        copied = contextvars.copy_context()
        copied.run(pop_context, previous)
        # Original context remains unchanged.
        self.assertEqual(get_chat_type(), "general")
        # Copied context was restored to defaults.
        self.assertEqual(copied.run(get_chat_type), "unknown")
