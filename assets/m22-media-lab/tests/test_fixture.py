"""The frozen fixture stays frozen, and its ground truth stays coherent."""

import hashlib
import json
import unittest

from support import KIT_ROOT

FIXTURE = KIT_ROOT / "fixture"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FixtureFilesTest(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((FIXTURE / "source-record.json").read_text())
        self.timeline = json.loads((FIXTURE / "timeline.json").read_text())

    def test_frozen_hashes_match(self):
        for name, expected in self.record["sha256"].items():
            self.assertEqual(sha256(FIXTURE / name), expected, name)

    def test_record_declares_synthetic_with_consent_and_retention(self):
        self.assertTrue(self.record["synthetic"])
        self.assertIn("No real person", self.record["consent"])
        self.assertTrue(self.record["retention"].strip())

    def test_timeline_lines_are_ordered_and_two_speaker(self):
        lines = self.timeline["lines"]
        self.assertEqual(len(lines), 15)
        self.assertEqual({ln["speaker"] for ln in lines}, {"agent", "caller"})
        for ln in lines:
            self.assertLess(ln["start"], ln["end"])

    def test_hold_silence_is_long_enough_to_separate_vad_from_windows(self):
        hold = self.timeline["hold_silence"]
        self.assertGreaterEqual(hold["end"] - hold["start"], 3.0)

    def test_overlap_region_sits_inside_both_lines(self):
        overlap = self.timeline["overlap"]
        caller = self.timeline["lines"][overlap["caller_line"]]
        agent = self.timeline["lines"][overlap["agent_line"]]
        start, end = overlap["region"]
        self.assertLess(start, end)
        for line in (caller, agent):
            self.assertLessEqual(line["start"], end)
            self.assertGreaterEqual(line["end"], start)

    def test_scenes_tile_the_recording(self):
        scenes = self.timeline["scenes"]
        self.assertEqual(len(scenes), 5)
        self.assertEqual(scenes[0]["start"], 0.0)
        for prev, cur in zip(scenes, scenes[1:]):
            self.assertEqual(prev["end"], cur["start"])
        self.assertEqual(scenes[-1]["end"], self.timeline["total_seconds"])


class KitHygieneTest(unittest.TestCase):
    def test_no_em_dash_anywhere_in_the_kit(self):
        offenders = []
        for path in KIT_ROOT.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".md", ".json", ".sh", ".ps1"}:
                if "work" in path.parts or "__pycache__" in path.parts:
                    continue
                if "\u2014" in path.read_text(encoding="utf-8", errors="ignore"):
                    offenders.append(str(path.relative_to(KIT_ROOT)))
        self.assertEqual(offenders, [])

    def test_no_personal_paths_in_committed_files(self):
        offenders = []
        for path in KIT_ROOT.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".md", ".json", ".sh", ".ps1"}:
                if "work" in path.parts or "__pycache__" in path.parts:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                if "/Users/" in text and "/System/Library" not in text:
                    offenders.append(str(path.relative_to(KIT_ROOT)))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
