"""The join validator refuses bad documents; speaker assignment is overlap-honest."""

import unittest

from support import segment
from join_transcript import SCHEMA_VERSION, assign_speaker, validate


def valid_doc():
    return {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "file": "call.mp4",
            "sha256": "abc",
            "synthetic": True,
            "consent": "synthetic fixture, no real person",
            "retention": "course lifetime",
        },
        "provenance": {"tools": ["test"], "joined_on": "2026-07-25"},
        "segments": [
            {**segment([("hi", 0.0, 0.3, 0.9)]), "speaker": "speaker_00"},
        ],
        "visual_events": [
            {"source_time": 1.0, "file": "frames/x.png", "sha256": "def",
             "reasons": ["periodic"], "ocr_lines": ["hello"]},
        ],
        "review": {"corrections_applied": [], "diarization_flags": {}},
        "derived_artifacts": ["transcript.json"],
    }


class ValidateTest(unittest.TestCase):
    def test_valid_document_passes(self):
        self.assertEqual(validate(valid_doc()), [])

    def test_missing_consent_is_refused(self):
        doc = valid_doc()
        del doc["source"]["consent"]
        self.assertTrue(any("consent" in p for p in validate(doc)))

    def test_empty_retention_is_refused(self):
        doc = valid_doc()
        doc["source"]["retention"] = "  "
        self.assertTrue(any("retention" in p for p in validate(doc)))

    def test_word_missing_probability_is_refused(self):
        doc = valid_doc()
        del doc["segments"][0]["words"][0]["probability"]
        self.assertTrue(any("probability" in p for p in validate(doc)))

    def test_wrong_schema_version_is_refused(self):
        doc = valid_doc()
        doc["schema_version"] = 99
        self.assertTrue(any("schema_version" in p for p in validate(doc)))


class AssignSpeakerTest(unittest.TestCase):
    TURNS = [
        {"speaker": "speaker_00", "start": 0.0, "end": 5.0},
        {"speaker": "speaker_01", "start": 5.0, "end": 9.0},
    ]

    def test_picks_the_turn_with_most_overlap(self):
        seg = {"start": 4.0, "end": 8.0}
        self.assertEqual(assign_speaker(seg, self.TURNS), "speaker_01")

    def test_no_overlap_is_unassigned_not_guessed(self):
        seg = {"start": 20.0, "end": 21.0}
        self.assertEqual(assign_speaker(seg, self.TURNS), "unassigned")


if __name__ == "__main__":
    unittest.main()
