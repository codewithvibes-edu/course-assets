"""Corrections preserve the machine's original hypothesis and splice cleanly."""

import unittest

from support import segment
from review_alignment import apply_correction, corrected_text


def corr(span, original, corrected):
    return {
        "span": span,
        "original": original,
        "corrected": corrected,
        "corrected_by": "test reviewer",
        "reason": "test",
    }


class ApplyCorrectionTest(unittest.TestCase):
    def test_marks_only_words_inside_the_span(self):
        seg = segment([("one", 1.0, 1.2, 0.9), ("seater", 1.2, 1.5, 0.7), ("box", 1.5, 1.8, 0.9)])
        hit = apply_correction(seg, corr([1.0, 1.5], "one seater", "one cedar"))
        self.assertTrue(hit)
        self.assertEqual(seg["words"][0]["original_hypothesis"], "one")
        self.assertEqual(seg["words"][1]["original_hypothesis"], "seater")
        self.assertNotIn("original_hypothesis", seg["words"][2])

    def test_original_hypothesis_survives_a_second_correction(self):
        seg = segment([("seater", 1.2, 1.5, 0.7)])
        apply_correction(seg, corr([1.2, 1.5], "seater", "cedar"))
        apply_correction(seg, corr([1.2, 1.5], "cedar", "cedar wood"))
        self.assertEqual(seg["words"][0]["original_hypothesis"], "seater")

    def test_returns_false_when_nothing_overlaps(self):
        seg = segment([("box", 1.5, 1.8, 0.9)])
        self.assertFalse(apply_correction(seg, corr([9.0, 9.5], "x", "y")))
        self.assertNotIn("applied_corrections", seg)


class CorrectedTextTest(unittest.TestCase):
    def test_splices_the_corrected_phrase_once(self):
        seg = segment([
            ("Order", 0.0, 0.4, 0.9),
            ("one", 1.0, 1.2, 0.9),
            ("seater", 1.2, 1.5, 0.7),
            ("box", 1.5, 1.8, 0.9),
        ])
        apply_correction(seg, corr([1.0, 1.5], "one seater", "one cedar"))
        self.assertEqual(corrected_text(seg), "Order one cedar box")

    def test_uncorrected_segment_renders_unchanged(self):
        seg = segment([("plain", 0.0, 0.4, 0.9), ("words", 0.4, 0.8, 0.9)])
        self.assertEqual(corrected_text(seg), "plain words")


if __name__ == "__main__":
    unittest.main()
