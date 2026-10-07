"""Identity, signed normalization and explicit target controls for dense interior data."""

import math
import tempfile
import unittest
from pathlib import Path

from fusion_public.cli import parser
from fusion_public.data import load_case
from fusion_public.dense_interior import PACKET_DIR, evaluate_dense, load_target, signed_scale


class DenseInteriorTests(unittest.TestCase):
    def test_both_dense_targets_and_grid_conventions(self):
        for target, b2 in (("reference401", 1.6293829620247962),
                           ("selected401", 1.6313464444829588)):
            packet, _ = load_target(target)
            self.assertEqual(packet["B2_scale_T2"], b2)
            self.assertEqual(packet["signed_target_flux_Wb"], -0.03141592653589793)
            self.assertEqual(packet["grid"]["s"], [0.25, 0.5, 0.75])
            self.assertFalse(packet["grid"]["realized_flux_labels"])
            for index, row in enumerate(packet["samples_xyz_B"]):
                self.assertAlmostEqual(math.atan2(row[1], row[0]),
                                       math.pi * (index // 64 % 64) / 64, places=13)

    def test_packet_and_manifest_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = (PACKET_DIR / "manifest.json").read_bytes()
            (root / "manifest.json").write_bytes(original)
            raw = (PACKET_DIR / "selected401.json").read_bytes()
            (root / "selected401.json").write_bytes(raw.replace(b"1.631346", b"1.531346", 1))
            with self.assertRaisesRegex(ValueError, "packet identity"):
                load_target("selected401", root)
            (root / "manifest.json").write_bytes(original + b" ")
            with self.assertRaisesRegex(ValueError, "manifest identity"):
                load_target("selected401", root)

    def test_signed_scale_preserves_orientation(self):
        self.assertEqual(signed_scale(-2.0, -6.0), 3.0)
        for measured in (0.0, 1.0, float("nan"), float("inf"), -1e-30):
            with self.assertRaises(ValueError):
                signed_scale(measured, -6.0)

    def test_explicit_target_and_budget(self):
        with self.assertRaisesRegex(ValueError, "registered target"):
            load_target("other")
        args = parser().parse_args(["dense-interior", "--target", "selected401",
                                    "--candidate", "candidate.json"])
        self.assertEqual(args.target, "selected401")
        case, _ = load_case()
        for seconds in (0, 601, True):
            with self.assertRaisesRegex(ValueError, "Budget"):
                evaluate_dense(case["seed"], case, "selected401", seconds)
