"""The deletion drill finds everything under work/ and reports honestly."""

import tempfile
import unittest
from pathlib import Path

from support import KIT_ROOT  # noqa: F401  (sys.path side effect)
import delete_derived


class CollectTest(unittest.TestCase):
    def setUp(self):
        self._orig = delete_derived.WORK_DIR
        self._tmp = tempfile.TemporaryDirectory()
        delete_derived.WORK_DIR = Path(self._tmp.name) / "work"

    def tearDown(self):
        delete_derived.WORK_DIR = self._orig
        self._tmp.cleanup()

    def test_missing_work_dir_collects_nothing(self):
        self.assertEqual(delete_derived.collect(), [])

    def test_finds_nested_derived_files(self):
        work = delete_derived.WORK_DIR
        (work / "frames").mkdir(parents=True)
        (work / "transcript.json").write_text("{}")
        (work / "frames" / "a.png").write_bytes(b"png")
        found = delete_derived.collect()
        self.assertEqual(
            sorted(p.name for p in found), ["a.png", "transcript.json"]
        )


class SampleFramesHelpersTest(unittest.TestCase):
    def test_showinfo_times_parse(self):
        import sample_frames

        stderr = "n:0 pts_time:0.0 x\nn:1 pts_time:19.1 y\nnothing here\n"
        self.assertEqual(sample_frames.showinfo_times(stderr), [0.0, 19.1])


if __name__ == "__main__":
    unittest.main()
