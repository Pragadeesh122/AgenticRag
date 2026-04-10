import os
import unittest
from unittest.mock import patch

from observability.hash import stable_hash


class StableHashTests(unittest.TestCase):
    def test_hash_is_deterministic_for_same_salt(self):
        with patch.dict(os.environ, {"OBSERVABILITY_HASH_SALT": "salt-a"}, clear=False):
            h1 = stable_hash("user-123")
            h2 = stable_hash("user-123")
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 16)

    def test_hash_changes_when_salt_changes(self):
        with patch.dict(os.environ, {"OBSERVABILITY_HASH_SALT": "salt-a"}, clear=False):
            h1 = stable_hash("user-123")
        with patch.dict(os.environ, {"OBSERVABILITY_HASH_SALT": "salt-b"}, clear=False):
            h2 = stable_hash("user-123")
        self.assertNotEqual(h1, h2)

    def test_empty_value_maps_to_unknown(self):
        self.assertEqual(stable_hash(None), "unknown")
        self.assertEqual(stable_hash(""), "unknown")

