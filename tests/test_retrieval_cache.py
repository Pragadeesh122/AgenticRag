import unittest

from pipeline.retrieval_cache import _escape_tag_value


class RetrievalCacheTagEscapingTests(unittest.TestCase):
    def test_uuid_dash_is_escaped_for_redisearch_tag_filter(self):
        project_id = "90ca197b-126a-43f4-a9a1-6b61a1a32716"
        escaped = _escape_tag_value(project_id)
        self.assertEqual(escaped, "90ca197b\\-126a\\-43f4\\-a9a1\\-6b61a1a32716")

    def test_alphanumeric_and_underscore_stay_unchanged(self):
        value = "project_123ABC"
        self.assertEqual(_escape_tag_value(value), value)

