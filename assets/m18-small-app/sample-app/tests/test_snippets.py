"""Tests for snip. Every test names the acceptance criterion it maps to;
the full mapping lives in test-map.md. Run from sample-app/:

    python3 -m unittest discover -s tests -v
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import snippets


class SnipTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = str(Path(self._tmp.name) / "snippets.json")

    def tearDown(self):
        self._tmp.cleanup()

    def test_add_and_list(self):
        """AC-1.1: a saved snippet shows up in the list with its tags."""
        snippets.add_snippet(self.store, "uv run python file.py", ["python", "uv"])
        lines = snippets.list_snippets(self.store)
        self.assertEqual(len(lines), 1)
        self.assertIn("uv run python file.py", lines[0])
        self.assertIn("python, uv", lines[0])

    def test_add_without_tags_lists_fine(self):
        """AC-1.2: tags are optional; an untagged snippet lists cleanly."""
        snippets.add_snippet(self.store, "git restore .", [])
        lines = snippets.list_snippets(self.store)
        self.assertEqual(len(lines), 1)
        self.assertIn("git restore .", lines[0])

    def test_search_matches_text_and_tags(self):
        """AC-2.2: search hits both text and tags, case-insensitive."""
        snippets.add_snippet(self.store, "lsof -i :8123", ["ports"])
        snippets.add_snippet(self.store, "log with graph", ["Git"])
        snippets.add_snippet(self.store, "git log --oneline", [])
        self.assertEqual(len(snippets.search_snippets(self.store, "LSOF")), 1)
        # one hit by text, a different one by tag, case-insensitive both ways
        self.assertEqual(len(snippets.search_snippets(self.store, "git")), 2)

    def test_list_filters_by_tag(self):
        """AC-2.1: --tag shows only snippets carrying that tag."""
        snippets.add_snippet(self.store, "one", ["a"])
        snippets.add_snippet(self.store, "two", ["b"])
        lines = snippets.list_snippets(self.store, tag="b")
        self.assertEqual(len(lines), 1)
        self.assertIn("two", lines[0])

    def test_empty_text_refused(self):
        """AC-U.2: empty text is refused with a deliberate message."""
        with self.assertRaises(SystemExit):
            snippets.add_snippet(self.store, "   ", [])

    def test_delete_missing_id_reports_cleanly(self):
        """AC-U.3: deleting a missing id reports, never silently ignores."""
        snippets.add_snippet(self.store, "keep me", [])
        with self.assertRaises(SystemExit):
            snippets.delete_snippet(self.store, 99)
        self.assertEqual(len(snippets.list_snippets(self.store)), 1)

    def test_corrupted_store_reports_cleanly(self):
        """AC-U.1: a hand-mangled store file is reported and refused,
        never silently overwritten."""
        Path(self.store).write_text("{not json", encoding="utf-8")
        with self.assertRaises(SystemExit):
            snippets.load_store(self.store)


if __name__ == "__main__":
    unittest.main()
