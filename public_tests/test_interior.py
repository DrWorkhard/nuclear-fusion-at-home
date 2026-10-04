"""Current normalization is separate from the bound fixed-current evaluator."""

import copy
import math
import unittest

from fusion_public.data import load_case
from fusion_public.interior import normalized_interior, vector_rms


class InteriorDiagnosticTests(unittest.TestCase):
    def test_vector_score_uses_fixed_target_scale_and_all_components(self):
        actual = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        target = [[2.0, 4.0, 6.0], [8.0, 10.0, 12.0]]
        self.assertEqual(vector_rms(actual, target, 7.0, 2.0), 0.0)
        self.assertAlmostEqual(vector_rms(actual, target, 7.0), math.sqrt(91 / 14))
        with self.assertRaises(ValueError):
            vector_rms(actual, target[:1], 7.0)

    def test_changed_reference_provenance_is_rejected(self):
        case, _ = load_case()
        case["provenance"]["parent_sha256"]["equilibrium_input"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "recorded parent"):
            normalized_interior(case["seed"], case)

    def test_seed_flux_already_matches_and_signed_ratios_are_preserved(self):
        case, _ = load_case()
        original = copy.deepcopy(case)
        reference = normalized_interior(case["seed"], case)
        self.assertEqual(case, original)
        self.assertEqual(reference["inner_points"], 64)
        self.assertAlmostEqual(reference["fixed_current_inner_vector_rms"],
                               0.3804347184, places=9)
        self.assertFalse(reference["physical_admission"])
        self.assertFalse(reference["step4_pass"])
        self.assertAlmostEqual(reference["flux_scale"], 1.0, places=12)
        self.assertAlmostEqual(reference["fixed_current_inner_vector_rms"],
                               reference["flux_normalized_inner_vector_rms"], places=12)
        doubled = copy.deepcopy(case)
        for row in doubled["physical"]:
            row["current"] *= 2
        changed = normalized_interior(doubled["seed"], doubled)
        self.assertAlmostEqual(changed["flux_scale"], 0.5, places=12)
        self.assertAlmostEqual(changed["flux_normalized_inner_vector_rms"],
                               reference["flux_normalized_inner_vector_rms"], places=12)
        self.assertNotAlmostEqual(changed["fixed_current_inner_vector_rms"],
                                  reference["fixed_current_inner_vector_rms"], places=3)
