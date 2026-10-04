"""Dense boundary rebuild agrees with the bundled sparse samples; fast checks only."""

import copy
import unittest

from fusion_public import dense
from fusion_public.data import load_case


class DenseBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.case, _ = load_case()
        self.document = dense.load_input(self.case)

    def test_rebuilt_grid_reproduces_every_bundled_boundary_sample(self):
        points, normals, weights = dense.boundary_grid(self.document)
        boundary = self.case["groups"]["boundary"]
        self.assertEqual(len(points), boundary["original_count"])
        for row, index in enumerate(boundary["indices"]):
            for got, want in ((points, "points_m"), (normals, "unit_normals")):
                for a, b in zip(got[index], boundary[want][row], strict=True):
                    self.assertLess(abs(a - b), 1e-12)
            self.assertLess(abs(weights[index] / boundary["weights"][row] - 1), 1e-10)

    def test_seed_current_is_the_flux_normalized_current(self):
        scale = dense.flux_scale(self.case["seed"], self.case, self.document)
        self.assertLess(abs(scale - 1), 1e-12)

    def test_flux_scale_is_inverse_to_uniform_current_scaling(self):
        doubled = copy.deepcopy(self.case)
        for row in doubled["physical"]:
            row["current"] *= 2
        scale = dense.flux_scale(self.case["seed"], doubled, self.document)
        self.assertLess(abs(scale - 0.5), 1e-12)

    def test_changed_reference_input_is_rejected(self):
        changed = copy.deepcopy(self.case)
        changed["provenance"]["parent_sha256"]["equilibrium_input"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "recorded parent"):
            dense.load_input(changed)
